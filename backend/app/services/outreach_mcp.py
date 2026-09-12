"""Read-only MCP tool surface for the outreach agents (Phase 2).

Loads tools from the optionally configured MCP server (for example a school
calendar) behind an explicit allowlist, so agents can only ever consume the
read-only tools named in settings. Loading is fail-safe: when the server is
unconfigured or unreachable, the agents run without MCP tools rather than with
unverified ones.
"""

import logging
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)


def parse_tool_allowlist(raw: str | None) -> list[str]:
    return [part.strip() for part in (raw or "").split(",") if part.strip()]


def mcp_enabled() -> bool:
    allowed = parse_tool_allowlist(getattr(settings, "mcp_allowed_tools", None))
    return bool(getattr(settings, "mcp_server_url", None) and allowed)


def build_tool_filters(allowed: list[str]) -> Any:
    from strands.tools.mcp import ToolFilters

    return ToolFilters(allowed=list(allowed))


class ReadonlyMcpTools:
    """Context manager yielding the allowlisted MCP tools while active.

    Entering starts the MCP client and loads only the allowlisted tools;
    exiting stops the client. Any failure is logged and degrades to zero
    tools (fail-safe) instead of surfacing unverified tools.
    """

    def __init__(self) -> None:
        self.tools: list[Any] = []
        self._client: Any = None

    def __enter__(self) -> "ReadonlyMcpTools":
        if mcp_enabled():
            try:
                from strands._async import run_async
                from strands.tools.mcp import MCPClient

                client = MCPClient(
                    url=settings.mcp_server_url,
                    tool_filters=build_tool_filters(
                        parse_tool_allowlist(settings.mcp_allowed_tools)
                    ),
                )
                client.start()
                self._client = client
                self.tools = list(run_async(client.load_tools()))
                if not self.tools:
                    logger.warning(
                        "MCP server %s exposed none of the allowlisted tools %s.",
                        settings.mcp_server_url,
                        parse_tool_allowlist(settings.mcp_allowed_tools),
                    )
                    self._stop_client()
                else:
                    logger.info(
                        "Loaded allowlisted MCP tools: %s",
                        [tool.tool_name for tool in self.tools],
                    )
            except Exception:
                logger.warning(
                    "MCP tool loading failed; continuing without MCP tools.",
                    exc_info=True,
                )
                self._stop_client()
                self.tools = []
        return self

    def __exit__(self, *exc_info: Any) -> None:
        self._stop_client()
        self.tools = []

    def _stop_client(self) -> None:
        if self._client is not None:
            try:
                self._client.stop()
            except Exception:
                logger.warning("MCP client shutdown failed.", exc_info=True)
        self._client = None
