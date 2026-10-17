from __future__ import annotations

import time

from collections.abc import Mapping
from typing import Any

import httpx
from pydantic import BaseModel, ConfigDict

from sandbox.domain.interfaces import (
    CommandExecutionResult,
    SandboxProvider,
    SandboxProviderInfo,
    SandboxProviderType,
)


class AIOAdapterConfig(BaseModel):
    """AIO provider 的专属配置"""

    model_config = ConfigDict(extra="forbid")

    image: str
    request_timeout_seconds: float = 5.0
    api_key: str | None = None


class AIOAdapter(SandboxProvider):
    """AIO 沙箱 Provider 适配器"""

    _HEALTH_FIELDS = frozenset(
        {"success", "message", "data", "home_dir", "version", "detail"}
    )

    def __init__(
        self,
        image: str,
        request_timeout_seconds: float,
        api_key: str | None = None,
    ) -> None:
        self._image = image
        self._request_timeout_seconds = request_timeout_seconds
        self._headers = {"X-AIO-API-Key": api_key} if api_key else {}

    @classmethod
    def sandbox_provider_id(cls) -> SandboxProviderType:
        return SandboxProviderType.AIO

    @classmethod
    def from_config(cls, config: Mapping[str, Any]) -> AIOAdapter:
        adapter_config = AIOAdapterConfig.model_validate(config)
        return cls(
            image=adapter_config.image,
            request_timeout_seconds=adapter_config.request_timeout_seconds,
            api_key=adapter_config.api_key,
        )

    def get_sandbox_provider_info(self) -> SandboxProviderInfo:
        return SandboxProviderInfo(image=self._image)

    async def check_ready(self, base_url: str | None) -> bool:
        # 预热阶段通过 AIO 健康接口确认容器内的服务已经可以接受命令。
        if base_url is None:
            return False

        try:
            async with httpx.AsyncClient(
                timeout=self._request_timeout_seconds,
                trust_env=False,
                headers=self._headers,
            ) as client:
                response = await client.get(f"{base_url.rstrip('/')}/v1/sandbox")
            if response.status_code != 200:
                return False
            payload = response.json()
        except (httpx.HTTPError, httpx.InvalidURL, ValueError):
            return False

        return isinstance(payload, dict) and self._HEALTH_FIELDS.issubset(payload)

    async def execute_command(
        self,
        base_url: str,
        command: str,
        working_directory: str,
        timeout_seconds: int,
    ) -> CommandExecutionResult:
        """通过 AIO Bash Pipe 执行命令并收集完整输出

        AIO 接口以异步 session 返回，因此通过 output 接口轮询增量输出
        本地超时后主动终止 session，避免只停止等待而让命令继续运行
        """
        url = base_url.rstrip("/")
        # 单次 HTTP 请求超时与命令总超时分开控制；deadline 约束整个执行过程
        request_timeout = max(self._request_timeout_seconds, 10.0)
        deadline = time.monotonic() + timeout_seconds
        async with httpx.AsyncClient(timeout=request_timeout, trust_env=False, headers=self._headers) as client:
            # async_mode 用于取得 session_id；hard_timeout 是 AIO 侧的超时兜底
            response = await client.post(
                f"{url}/v1/bash/exec",
                json={
                    "command": command,
                    "exec_dir": working_directory,
                    "async_mode": True,
                    "hard_timeout": timeout_seconds,
                },
            )
            response.raise_for_status()
            payload = response.json()
            data = payload.get("data") if isinstance(payload, dict) else None
            if not isinstance(data, dict) or not payload.get("success"):
                raise RuntimeError("AIO Bash returned an invalid command result")

            session_id = data.get("session_id")
            if not isinstance(session_id, str) or not session_id:
                raise RuntimeError("AIO Bash did not return a command session id")
            command_id = data.get("command_id")
            # exec 可能已经返回首批输出，后续只从 offset 之后读取，避免重复拼接
            stdout_parts = [data.get("stdout") or ""]
            stderr_parts = [data.get("stderr") or ""]
            stdout_offset = int(data.get("offset") or len(stdout_parts[0].encode("utf-8")))
            stderr_offset = int(data.get("stderr_offset") or len(stderr_parts[0].encode("utf-8")))
            status = data.get("status")
            exit_code = data.get("exit_code")

            while status not in {"completed", "timed_out", "killed"}:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    # 本地超时后主动发送 SIGKILL
                    # 即使请求失败，AIO 的 hard_timeout 仍会限制命令最长运行时间
                    try:
                        kill_response = await client.post(
                            f"{url}/v1/bash/kill",
                            json={"session_id": session_id, "signal": "SIGKILL"},
                        )
                        kill_response.raise_for_status()
                    except httpx.HTTPError:
                        # 显式终止失败时依赖 AIO 侧 hard_timeout，避免命令无限运行
                        pass
                    return CommandExecutionResult(
                        stdout="".join(stdout_parts),
                        stderr="".join(stderr_parts),
                        exit_code=exit_code,
                        timed_out=True,
                    )

                # 通过 stdout/stderr offset 获取新增输出，并等待命令状态变化。
                output_response = await client.post(
                    f"{url}/v1/bash/output",
                    json={
                        "session_id": session_id,
                        "command_id": command_id,
                        "offset": stdout_offset,
                        "stderr_offset": stderr_offset,
                        "wait": True,
                        "wait_timeout": min(1, max(0.1, remaining)),
                    },
                )
                output_response.raise_for_status()
                output_payload = output_response.json()
                output_data = output_payload.get("data") if isinstance(output_payload, dict) else None
                if not isinstance(output_data, dict) or not output_payload.get("success"):
                    raise RuntimeError("AIO Bash returned an invalid command output")
                stdout = output_data.get("stdout") or ""
                stderr = output_data.get("stderr") or ""
                stdout_parts.append(stdout)
                stderr_parts.append(stderr)
                stdout_offset = int(output_data.get("offset") or stdout_offset + len(stdout.encode("utf-8")))
                stderr_offset = int(output_data.get("stderr_offset") or stderr_offset + len(stderr.encode("utf-8")))
                status = output_data.get("status", status)
                exit_code = output_data.get("exit_code", exit_code)

            return CommandExecutionResult(
                stdout="".join(stdout_parts),
                stderr="".join(stderr_parts),
                exit_code=exit_code,
                timed_out=status == "timed_out",
            )