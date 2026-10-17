from __future__ import annotations

from datetime import datetime, timezone

from common.core.exceptions import ServiceException

from sandbox.application.workspace_manager import WorkspaceManager
from sandbox.core.providers import SandboxProviderManager
from sandbox.domain.entities import SandboxState
from sandbox.domain.error_codes import SandboxErrorCode
from sandbox.domain.repositories import SandboxRepository, WorkspaceRepository
from sandbox.domain.interfaces import CommandExecutionResult


class CommandExecutor:
    """Resolve a user's session workspace and execute a command via its provider."""

    def __init__(
        self,
        sandbox_repository: SandboxRepository,
        workspace_repository: WorkspaceRepository,
        workspace_manager: WorkspaceManager,
        sandbox_provider_manager: SandboxProviderManager,
    ) -> None:
        self._sandbox_repository = sandbox_repository
        self._workspace_repository = workspace_repository
        self._workspace_manager = workspace_manager
        self._sandbox_provider_manager = sandbox_provider_manager

    async def execute(
        self,
        *,
        user_id: str,
        session_id: str,
        command: str,
        timeout_seconds: int,
    ) -> CommandExecutionResult:
        workspace_id = await self._workspace_manager.allocate(user_id, session_id)
        workspace = await self._workspace_repository.get_by_id(workspace_id)
        if workspace is None or not workspace.sandbox_id or not workspace.workspace_path:
            raise ServiceException(
                SandboxErrorCode.SANDBOX_UNLOADING,
                "session workspace is not attached to an active sandbox",
            )

        sandbox = await self._sandbox_repository.get_by_id(workspace.sandbox_id)
        if (
            sandbox is None
            or sandbox.state != SandboxState.USER_ACTIVE
            or sandbox.bind_user_id != user_id
            or not sandbox.base_url
        ):
            raise ServiceException(
                SandboxErrorCode.SANDBOX_UNLOADING,
                "user sandbox is not available for command execution",
            )

        active = await self._sandbox_repository.record_activity(
            sandbox.sandbox_id, user_id, datetime.now(timezone.utc),
        )
        if active is None:
            raise ServiceException(
                SandboxErrorCode.SANDBOX_UNLOADING,
                "sandbox became unavailable before command execution",
            )

        return await self._sandbox_provider_manager.execute_command(
            provider_id=sandbox.provider_id,
            base_url=sandbox.base_url,
            command=command,
            working_directory=workspace.workspace_path,
            timeout_seconds=timeout_seconds,
        )