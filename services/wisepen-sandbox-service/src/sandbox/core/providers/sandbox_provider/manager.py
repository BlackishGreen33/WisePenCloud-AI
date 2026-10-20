from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from sandbox.domain.interfaces import (
    ProviderCommandHandle,
    ProviderCommandSnapshot,
    SandboxProvider,
    SandboxProvision,
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

    def create_provision(self, provider_id: str | SandboxProviderType) -> SandboxProvision:
        return self._get(provider_id).create_provision()

    def _get(self, provider_id: str | SandboxProviderType) -> SandboxProvider:
        provider = self._providers.get(SandboxProviderType(provider_id))
        if provider is None:
            raise ValueError(f"sandbox provider is not configured: {provider_id}")
        return provider

    async def check_ready(self, provider_id: str, base_url: str | None, provider_metadata: Mapping[str, Any] | None = None) -> bool:
        provider = self._providers.get(SandboxProviderType(provider_id))
        return False if provider is None else await provider.check_ready(base_url, provider_metadata)

    async def start_command(self, provider_id: str, base_url: str, command: str, working_directory: str, timeout_seconds: int, provider_metadata: Mapping[str, Any] | None = None) -> ProviderCommandHandle:
        return await self._get(provider_id).start_command(base_url, command, working_directory, timeout_seconds, provider_metadata)

    async def get_command_result(self, provider_id: str, base_url: str, handle: ProviderCommandHandle, stdout_offset: int, stderr_offset: int, wait_timeout_seconds: float, provider_metadata: Mapping[str, Any] | None = None) -> ProviderCommandSnapshot:
        return await self._get(provider_id).get_command_result(base_url, handle, stdout_offset, stderr_offset, wait_timeout_seconds, provider_metadata)

    async def kill_command(self, provider_id: str, base_url: str, handle: ProviderCommandHandle, provider_metadata: Mapping[str, Any] | None = None) -> None:
        await self._get(provider_id).kill_command(base_url, handle, provider_metadata)