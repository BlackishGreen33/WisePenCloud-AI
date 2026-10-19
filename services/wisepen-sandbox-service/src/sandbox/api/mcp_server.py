from __future__ import annotations

from collections.abc import Mapping
from typing import Annotated

from mcp.server.fastmcp import Context, FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from pydantic import Field

from sandbox.application.command_task_service import CommandTaskService
from sandbox.domain.entities import CommandTaskDocument


MAX_COMMAND_TIMEOUT_SECONDS = 600

WISEPEN_TOOL_CONFIG_META_KEY = "com.wisepen/tool_config"
WISEPEN_TOOL_CONTEXT_META_KEY = "com.wisepen/tool_context"

def get_tool_config_value(ctx: Context, key: str) -> object | None:
    meta = ctx.request_context.meta
    if not meta:
        return None
    tool_config = (meta.model_extra or {}).get(WISEPEN_TOOL_CONFIG_META_KEY)
    return tool_config.get(key) if isinstance(tool_config, Mapping) else None

def get_tool_context_value(ctx: Context, key: str) -> object | None:
    meta = ctx.request_context.meta
    if not meta:
        return None
    tool_context = (meta.model_extra or {}).get(WISEPEN_TOOL_CONTEXT_META_KEY)
    return tool_context.get(key) if isinstance(tool_context, Mapping) else None

def _result(task: CommandTaskDocument) -> dict[str, str | int | bool | None]:
    return {
        "task_id": task.task_id,
        "status": task.status.value,
        "stdout": task.stdout,
        "stderr": task.stderr,
        "output_truncated": task.output_truncated,
        "exit_code": task.exit_code,
        "error": task.error,
    }


def create_sandbox_mcp_server(task_service: CommandTaskService) -> FastMCP:
    mcp = FastMCP(
        "wisepen-sandbox-service",
        stateless_http=True,
        json_response=True,
        streamable_http_path="/",
        transport_security=TransportSecuritySettings(
            enable_dns_rebinding_protection=False
        ),
    )

    @mcp.tool(
        name="start_command",
        description="Start a shell command in a user's session workspace and return its task ID without waiting.",
    )
    async def start_command(
        ctx: Context,
        command: Annotated[str, Field(min_length=1, description="Shell command to execute.")],
        timeout_seconds: Annotated[int, Field(ge=1, le=MAX_COMMAND_TIMEOUT_SECONDS)] = 60,
    ) -> dict[str, str]:
        task = await task_service.start_command(
            user_id=get_tool_context_value(ctx, "user_id"),
            session_id=get_tool_context_value(ctx, "session_id"),
            command=command,
            timeout_seconds=timeout_seconds,
        )
        return {"task_id": task.task_id, "status": task.status.value}

    @mcp.tool(
        name="get_command_result",
        description="Get a command task result, optionally waiting for completion.",
    )
    async def get_command_result(
        task_id: Annotated[str, Field(min_length=1, description="Random command task ID.")],
        wait: Annotated[bool, Field(description="Wait for the task to finish, up to wait_timeout_seconds.")] = False,
        wait_timeout_seconds: Annotated[float, Field(ge=0, le=MAX_COMMAND_TIMEOUT_SECONDS)] = 0,
    ) -> dict[str, str | int | bool | None]:
        task = await task_service.get_command_result(
            task_id,
            wait=wait,
            wait_timeout_seconds=wait_timeout_seconds,
        )
        return _result(task)

    @mcp.tool(
        name="kill_command",
        description="Request termination of a running command task. A successful response means AIO accepted the request; it does not wait for remote process confirmation.",
    )
    async def kill_command(
        task_id: Annotated[str, Field(min_length=1, description="Random command task ID.")],
    ) -> dict[str, str]:
        task = await task_service.kill_command(task_id)
        return {"task_id": task.task_id, "status": task.status.value}

    @mcp.tool(
        name="execute_command",
        description="Execute a shell command in a user's session workspace and wait for its final result.",
    )
    async def execute_command(
        ctx: Context,
        command: Annotated[str, Field(min_length=1, description="Shell command to execute.")],
        timeout_seconds: Annotated[int, Field(ge=1, le=MAX_COMMAND_TIMEOUT_SECONDS)] = 60,
    ) -> dict[str, str | int | bool | None]:
        task = await task_service.execute_command(
            user_id=get_tool_context_value(ctx, "user_id"),
            session_id=get_tool_context_value(ctx, "session_id"),
            command=command,
            timeout_seconds=timeout_seconds,
        )
        return _result(task)

    return mcp