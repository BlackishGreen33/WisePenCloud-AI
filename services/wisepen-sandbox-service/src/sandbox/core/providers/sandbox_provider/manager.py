from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from sandbox.domain.interfaces import (
    ProviderCommandHandle,
    ProviderCommandSnapshot,
    SandboxProvider,
    SandboxProviderInfo,
    SandboxProviderType,
)


class SandboxProviderManager:
    """按 provider_id 管理并路由沙箱生命周期和命令能力。"""

    def __init__(self, provider_classes: Sequence[type[SandboxProvider]], provider_settings: dict[SandboxProviderType, dict[str, Any]]) -> None:
        self._providers: dict[SandboxProviderType, SandboxProvider] = {}
        for provider_class in provider_classes:
            provider_id = provider_class.sandbox_provider_id()
            config = provider_settings.get(provider_id)
            if config is not None:
                self._providers[provider_id] = provider_class.from_config(config)

    def get_provider_info(self, provider_id: str | SandboxProviderType) -> SandboxProviderInfo:
        return self._providers[SandboxProviderType(provider_id)].get_sandbox_provider_info()

    def _get(self, provider_id: str | SandboxProviderType) -> SandboxProvider:
        provider = self._providers.get(SandboxProviderType(provider_id))
        if provider is None:
            raise ValueError(f"sandbox provider is not configured: {provider_id}")
        return provider

    async def check_ready(self, provider_id: str, base_url: str | None) -> bool:
        provider = self._providers.get(SandboxProviderType(provider_id))
        return False if provider is None else await provider.check_ready(base_url)

    async def start_command(self, provider_id: str, base_url: str, command: str, working_directory: str, timeout_seconds: int) -> ProviderCommandHandle:
        return await self._get(provider_id).start_command(base_url, command, working_directory, timeout_seconds)

    async def get_command_result(self, provider_id: str, base_url: str, handle: ProviderCommandHandle, stdout_offset: int, stderr_offset: int, wait_timeout_seconds: float) -> ProviderCommandSnapshot:
        return await self._get(provider_id).get_command_result(base_url, handle, stdout_offset, stderr_offset, wait_timeout_seconds)

    async def kill_command(self, provider_id: str, base_url: str, handle: ProviderCommandHandle) -> None:
        await self._get(provider_id).kill_command(base_url, handle)