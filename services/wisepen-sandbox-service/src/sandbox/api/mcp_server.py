from __future__ import annotations

from typing import Annotated

from mcp.server.fastmcp import FastMCP
from pydantic import Field

from sandbox.application.command_executor import CommandExecutor


MAX_COMMAND_TIMEOUT_SECONDS = 600


def create_sandbox_mcp_server(command_executor: CommandExecutor) -> FastMCP:
    server = FastMCP(
        "wisepen-sandbox-service",
        stateless_http=True,
        json_response=True,
        streamable_http_path="/",
    )

    @server.tool(
        name="execute_command",
        description="Execute a shell command in the calling user's session workspace. "
        "Returns stdout, stderr, exit code, and whether the command timed out. "
        "AIO enforces a hard timeout and terminates the command when it expires.",
    )
    async def execute_command(
        user_id: Annotated[str, Field(min_length=1, description="User that owns the sandbox.")],
        session_id: Annotated[str, Field(min_length=1, description="Session whose workspace is the working directory.")],
        command: Annotated[str, Field(min_length=1, description="Shell command to execute.")],
        timeout_seconds: Annotated[int, Field(ge=1, le=MAX_COMMAND_TIMEOUT_SECONDS)] = 60,
    ) -> dict[str, str | int | bool | None]:
        result = await command_executor.execute(
            user_id=user_id,
            session_id=session_id,
            command=command,
            timeout_seconds=timeout_seconds,
        )
        return result.model_dump()

    return server