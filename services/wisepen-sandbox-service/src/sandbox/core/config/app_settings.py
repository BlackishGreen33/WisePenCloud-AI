from __future__ import annotations

import asyncio
import os
import threading
from typing import Any, Literal

import yaml
from common.logger import error, info
from pydantic import BaseModel, ConfigDict, Field, model_validator

from sandbox.core.config.nacos import nacos_client_manager
from sandbox.domain.interfaces import SandboxProviderType


class AppSettings(BaseModel):
    """沙箱池核心运行配置。

    这些配置只覆盖 core 的池容量、warmup、销毁、重试和鉴权参数。应用启动
    前会由 Nacos 提供完整配置。Mongo 配置用于持久化 sandbox/workspace 权威状态，
    Workspace 配置用于受管目录、快照缓存和后台淘汰策略。
    """

    model_config = ConfigDict(extra="forbid")

    # 内部调用鉴权与 Mongo 权威存储配置。
    FROM_SOURCE_SECRET: str
    MONGODB_URL: str
    MONGODB_DB_NAME: str
    REDIS_URL: str

    # sandbox 池容量、warmup、销毁和重试配置。
    SANDBOX_ACTIVE_PROVIDER_ID: SandboxProviderType
    SANDBOX_PROVIDER_SETTINGS: dict[SandboxProviderType, dict[str, Any]]
    SANDBOX_TARGET_READY: int = 5

    # AIO 容器运行时参数。
    SANDBOX_DOCKER_SECCOMP_PROFILE: str = "unconfined"
    SANDBOX_DOCKER_SHM_SIZE: str = "2g"

    # READY 容器最长保留时间；超时后滚动替换，避免长期运行的空闲容器持续占用磁盘。
    SANDBOX_READY_MAX_AGE_SECONDS: float = Field(default=21600, gt=0)

    # 宿主机容器存储文件系统保护：达到高水位或低于最小剩余空间时停止扩池并回收未分配容器；
    # 使用率回落到低水位且剩余空间恢复后解除保护。该路径由当前 Docker daemon 在宿主机上解析。
    # 探针对该路径执行 df，读取承载该目录的整个文件系统容量，而不是计算目录自身的文件大小。
    # 默认沿用部署环境的 containerd 数据目录；若 Docker Root Dir 位于其他独立磁盘，应改为实际路径。
    SANDBOX_HOST_CONTAINER_STORAGE_PATH: str = "/var/lib/containerd"
    SANDBOX_HOST_RESOURCE_PROBE_IMAGE: str = "busybox:1.37"
    SANDBOX_CPU_SAMPLE_SECONDS: float = Field(default=1.0, gt=0, le=10)
    SANDBOX_CPU_HIGH_WATERMARK_PERCENT: float = Field(default=90.0, gt=0, le=100)
    SANDBOX_CPU_LOW_WATERMARK_PERCENT: float = Field(default=75.0, ge=0, lt=100)
    SANDBOX_DISK_HIGH_WATERMARK_PERCENT: float = Field(default=85.0, gt=0, lt=100)
    SANDBOX_DISK_LOW_WATERMARK_PERCENT: float = Field(default=80.0, ge=0, lt=100)
    SANDBOX_DISK_MIN_FREE_BYTES: int = Field(default=50 * 1024 * 1024 * 1024, ge=0)

    # 预热超时时间
    SANDBOX_WARMUP_TIMEOUT_SECONDS: float
    # 销毁超时时间
    SANDBOX_DESTROY_TIMEOUT_SECONDS: float
    # 预热最大尝试次数
    SANDBOX_WARMUP_MAX_RETRIES: int

    # 状态检查时间间隔
    SANDBOX_WATCHER_INTERVAL_SECONDS: float

    # 用户沙箱在此时长内无命令请求后进入回收流程。
    SANDBOX_IDLE_TIMEOUT_SECONDS: float = 1800

    # 单个任务 stdout 与 stderr 的合计保存上限。
    SANDBOX_COMMAND_OUTPUT_MAX_BYTES: int = 65536

    # AIO File 与 OSS 间单文件传输限制及临时缓冲配置。
    SANDBOX_FILE_MAX_BYTES: int = 100 * 1024 * 1024
    SANDBOX_FILE_SPOOL_MAX_MEMORY_BYTES: int = 8 * 1024 * 1024
    SANDBOX_FILE_DOWNLOAD_URL_DURATION_SECONDS: int = 900
    SANDBOX_FILE_TRANSFER_TIMEOUT_SECONDS: float = 120.0

    # File Storage 内部 RPC / 服务发现。
    RPC_LB_STRATEGY: Literal["weighted_random", "round_robin", "random"] = "weighted_random"
    RPC_DEFAULT_TIMEOUT: float = 5.0
    RPC_DEFAULT_RETRIES: int = 2
    SERVICE_DISCOVERY_CACHE_TTL_SECONDS: float = 30.0

    # Sandbox-service 容器内访问 Docker host 发布端口的地址。
    SANDBOX_DOCKER_HOST: str | None = None

    # session 的容器目录与磁盘缓存目录。
    SANDBOX_CONTAINER_WORKSPACE_ROOT: str = "./data/workspaces"
    SANDBOX_WORKSPACE_EXPORT_ROOT: str = "./data/workspace-cache"

    @model_validator(mode="after")
    def validate_sandbox_runtime_limits(self) -> AppSettings:
        if self.SANDBOX_DISK_LOW_WATERMARK_PERCENT >= self.SANDBOX_DISK_HIGH_WATERMARK_PERCENT:
            raise ValueError("SANDBOX_DISK_LOW_WATERMARK_PERCENT must be lower than the high watermark")
        if self.SANDBOX_CPU_LOW_WATERMARK_PERCENT >= self.SANDBOX_CPU_HIGH_WATERMARK_PERCENT:
            raise ValueError("SANDBOX_CPU_LOW_WATERMARK_PERCENT must be lower than the high watermark")
        for name in (
            "SANDBOX_DOCKER_SECCOMP_PROFILE",
            "SANDBOX_DOCKER_SHM_SIZE",
            "SANDBOX_HOST_CONTAINER_STORAGE_PATH",
            "SANDBOX_HOST_RESOURCE_PROBE_IMAGE",
        ):
            if not getattr(self, name).strip():
                raise ValueError(f"{name} must not be empty")
        return self


def _run_async(coro):
    """在新线程的独立事件循环中执行协程，兼容 uvicorn 启动时已有运行中事件循环的场景。"""
    result, exc = None, None

    def _target():
        nonlocal result, exc
        try:
            result = asyncio.run(coro)
        except Exception as e:
            exc = e

    t = threading.Thread(target=_target)
    t.start()
    t.join()
    if exc:
        raise exc
    return result


def load_settings() -> AppSettings:
    """从 Nacos 拉取 sandbox core 配置并构造 AppSettings。"""

    try:
        # 当前服务启动严格依赖 Nacos 配置；拉取失败直接暴露启动错误。
        info("nacos app config pulling.")
        raw_yaml = _run_async(nacos_client_manager.pull_config())
        config_dict = yaml.safe_load(raw_yaml) if raw_yaml else {}
        config_dict = config_dict or {}
        # Docker 发布端口的宿主机地址属于部署环境配置，可由 Compose 环境变量覆盖 Nacos 默认值。
        docker_host = os.getenv("SANDBOX_DOCKER_HOST")
        if docker_host:
            config_dict["SANDBOX_DOCKER_HOST"] = docker_host
        return AppSettings(**config_dict)
    except Exception as e:
        error("nacos app config pull failed.", exc=e)
        raise

settings = load_settings()
