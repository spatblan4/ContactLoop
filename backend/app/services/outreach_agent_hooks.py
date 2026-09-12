"""Hooks that turn the outreach agent's read-only safety boundary into an
SDK-enforced guarantee.

The agent may only call tools in an explicit whitelist. Any other tool call is
cancelled before execution and logged, so a prompt-level rule ("never write
follow-ups") becomes a code-level guarantee enforced by the Strands event loop.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class ReadOnlyToolGuard:
    """Structural HookProvider that blocks non-whitelisted tool calls.

    Implements the Strands ``HookProvider`` protocol (``register_hooks``) without
    importing strands at module import time, so this module stays importable in
    environments that have not installed the optional Bedrock dependencies.
    """

    def __init__(self, allowed_tools: Any) -> None:
        self.allowed_tools = frozenset(allowed_tools)

    def register_hooks(self, registry: Any, **kwargs: Any) -> None:
        from strands.hooks import AfterToolCallEvent, BeforeToolCallEvent

        registry.add_callback(BeforeToolCallEvent, self._before_tool_call)
        registry.add_callback(AfterToolCallEvent, self._after_tool_call)

    def _before_tool_call(self, event: Any) -> None:
        tool_name = (event.tool_use or {}).get("name")
        if tool_name not in self.allowed_tools:
            logger.warning(
                "Blocked non-whitelisted agent tool call: %s (allowed: %s)",
                tool_name,
                sorted(self.allowed_tools),
            )
            event.cancel_tool = f"tool '{tool_name}' is not allowed for this agent"

    def _after_tool_call(self, event: Any) -> None:
        tool_name = (event.tool_use or {}).get("name")
        if event.cancel_message:
            logger.info(
                "Agent tool call %s cancelled: %s", tool_name, event.cancel_message
            )
        elif event.exception is not None:
            logger.warning(
                "Agent tool call %s failed.",
                tool_name,
                exc_info=event.exception,
            )
        else:
            logger.info(
                "Agent tool call %s completed in %.0f ms",
                tool_name,
                (event.duration or 0) * 1000,
            )
