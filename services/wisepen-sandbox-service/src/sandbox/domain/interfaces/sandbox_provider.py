from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class SandboxProviderType(StrEnum):
    AIO = "AIO"


class ProviderCommandHandle(BaseModel):
    """Provider 内部命令句柄，不作为 MCP 对外 ID"""

    provider_session_id: str
    provider_command_id: str | None = None


class ProviderCommandSnapshot(BaseModel):
    """一次命令状态读取结果；stdout/stderr 是本次读取到的增量"""

    status: str
    stdout: str = ""
    stderr: str = ""
    stdout_offset: int = 0
    stderr_offset: int = 0
    exit_code: int | None = None


class SandboxProviderInfo(BaseModel):
    image: str = Field(..., description="容器镜像名称")


class SandboxProvider(ABC):
    """沙箱生命周期和命令能力的统一 Provider 扩展点"""

    @classmethod
    @abstractmethod
    def sandbox_provider_id(cls) -> SandboxProviderType:
        pass

    @classmethod
    @abstractmethod
    def from_config(cls, config: Mapping[str, Any]) -> SandboxProvider:
        pass

    @abstractmethod
    def get_sandbox_provider_info(self) -> SandboxProviderInfo:
        pass

    @abstractmethod
    async def check_ready(self, base_url: str | None) -> bool:
        pass

    @abstractmethod
    async def start_command(
        self,
        base_url: str,
        command: str,
        working_directory: str,
        timeout_seconds: int,
    ) -> ProviderCommandHandle:
        pass

    @abstractmethod
    async def get_command_result(
        self,
        base_url: str,
        handle: ProviderCommandHandle,
        stdout_offset: int,
        stderr_offset: int,
        wait_timeout_seconds: float,
    ) -> ProviderCommandSnapshot:
        pass

    @abstractmethod
    async def kill_command(self, base_url: str, handle: ProviderCommandHandle) -> None:
        pass