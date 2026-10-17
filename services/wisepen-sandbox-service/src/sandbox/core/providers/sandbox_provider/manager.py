from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from sandbox.domain.interfaces import CommandExecutionResult, SandboxProvider, SandboxProviderInfo, SandboxProviderType


class SandboxProviderManager:
    """按 provider_id 管理并路由 sandbox provider"""

    def __init__(
            self,
            provider_classes: Sequence[type[SandboxProvider]],
            provider_settings: dict[SandboxProviderType, dict[str, Any]],
    ) -> None:
        self._providers: dict[SandboxProviderType, SandboxProvider] = {}
        for provider_class in provider_classes:
            provider_id = provider_class.sandbox_provider_id()
            config = provider_settings.get(provider_id)
            if config is not None:
                self._providers[provider_id] = provider_class.from_config(config)

    def get_provider_info(self, provider_id: str | SandboxProviderType) -> SandboxProviderInfo:
        return self._providers[SandboxProviderType(provider_id)].get_sandbox_provider_info()

    async def check_ready(self, provider_id: str, base_url: str | None) -> bool:
        provider = self._providers.get(SandboxProviderType(provider_id))
        if provider is None: return False
        return await provider.check_ready(base_url)

    async def execute_command(
        self,
        provider_id: str | SandboxProviderType,
        base_url: str,
        command: str,
        working_directory: str,
        timeout_seconds: int,
    ) -> CommandExecutionResult:
        provider = self._providers.get(SandboxProviderType(provider_id))
        if provider is None:
            raise ValueError(f"sandbox provider is not configured: {provider_id}")
        return await provider.execute_command(
            base_url=base_url,
            command=command,
            working_directory=working_directory,
            timeout_seconds=timeout_seconds,
        )