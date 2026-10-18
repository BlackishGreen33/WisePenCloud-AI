from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import httpx
from pydantic import BaseModel, ConfigDict

from sandbox.domain.interfaces import (
    ProviderCommandHandle,
    ProviderCommandSnapshot,
    SandboxProvider,
    SandboxProviderInfo,
    SandboxProviderType,
)


class AIOAdapterConfig(BaseModel):
    """AIO Provider 的专属配置"""

    model_config = ConfigDict(extra="forbid")

    image: str
    request_timeout_seconds: float = 5.0
    api_key: str | None = None


class AIOAdapter(SandboxProvider):
    """AIO 沙箱 Provider 适配器"""

    _HEALTH_FIELDS = frozenset({"success", "message", "data", "home_dir", "version", "detail"})

    def __init__(self, image: str, request_timeout_seconds: float, api_key: str | None = None) -> None:
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
        # 预热阶段通过 AIO 健康接口确认容器内服务已经可以接受命令
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

    async def start_command(
        self,
        base_url: str,
        command: str,
        working_directory: str,
        timeout_seconds: int,
    ) -> ProviderCommandHandle:
        """通过 AIO Bash Pipe 启动命令并返回 Provider 句柄

        命令以异步 session 启动，后续状态和输出由 get_command_result 读取
        hard_timeout 由 AIO 负责兜底终止命令
        """
        async with httpx.AsyncClient(
            timeout=self._request_timeout_seconds,
            trust_env=False,
            headers=self._headers,
        ) as client:
            response = await client.post(
                f"{base_url.rstrip('/')}/v1/bash/exec",
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
            raise RuntimeError("AIO Bash returned an invalid command handle")
        session_id = data.get("session_id")
        if not isinstance(session_id, str) or not session_id:
            raise RuntimeError("AIO Bash did not return a command session id")
        command_id = data.get("command_id")
        return ProviderCommandHandle(
            provider_session_id=session_id,
            provider_command_id=command_id if isinstance(command_id, str) else None,
        )

    async def get_command_result(
        self,
        base_url: str,
        handle: ProviderCommandHandle,
        stdout_offset: int,
        stderr_offset: int,
        wait_timeout_seconds: float,
    ) -> ProviderCommandSnapshot:
        """读取 AIO 命令的增量输出和状态"""
        async with httpx.AsyncClient(
            timeout=max(self._request_timeout_seconds, wait_timeout_seconds + 2),
            trust_env=False,
            headers=self._headers,
        ) as client:
            response = await client.post(
                f"{base_url.rstrip('/')}/v1/bash/output",
                json={
                    "session_id": handle.provider_session_id,
                    "command_id": handle.provider_command_id,
                    "offset": stdout_offset,
                    "stderr_offset": stderr_offset,
                    "wait": True,
                    "wait_timeout": wait_timeout_seconds,
                },
            )
            response.raise_for_status()
            payload = response.json()
        data = payload.get("data") if isinstance(payload, dict) else None
        if not isinstance(data, dict) or not payload.get("success"):
            raise RuntimeError("AIO Bash returned an invalid command result")
        stdout = data.get("stdout") or ""
        stderr = data.get("stderr") or ""
        return ProviderCommandSnapshot(
            status=str(data.get("status") or "running"),
            stdout=stdout,
            stderr=stderr,
            stdout_offset=int(data.get("offset") or stdout_offset + len(stdout.encode("utf-8"))),
            stderr_offset=int(data.get("stderr_offset") or stderr_offset + len(stderr.encode("utf-8"))),
            exit_code=data.get("exit_code"),
        )

    async def kill_command(self, base_url: str, handle: ProviderCommandHandle) -> None:
        """主动终止 AIO 命令"""
        async with httpx.AsyncClient(
            timeout=self._request_timeout_seconds,
            trust_env=False,
            headers=self._headers,
        ) as client:
            response = await client.post(
                f"{base_url.rstrip('/')}/v1/bash/kill",
                json={"session_id": handle.provider_session_id, "signal": "SIGKILL"},
            )
            response.raise_for_status()
            # HTTP 200 只代表请求已到达，业务层拒绝终止时仍需向调用方报错
            payload = response.json()
            if not isinstance(payload, dict) or payload.get("success") is not True:
                raise RuntimeError("AIO Bash rejected command termination")
