"""A scripted Strands Model implementation for driving the real agent loop.

The fake replays a list of scripted assistant turns through the exact
StreamEvent protocol used by the Strands event loop (messageStart /
contentBlockStart / contentBlockDelta / contentBlockStop / messageStop /
metadata), so tests exercise real tool execution, hooks, and structured
output parsing without any network access.
"""

import json
from typing import Any

from strands.models.model import Model


class FakeModel(Model):
    """Structural implementation of the Strands ``Model`` interface."""

    stateful = False

    def __init__(self, turns: list[dict], structured: Any = None):
        self.turns = list(turns)
        self.structured = structured
        self.config: dict[str, Any] = {}
        self.stream_requests: list[dict] = []

    # -- Model interface ---------------------------------------------------

    def update_config(self, **model_config: Any) -> None:
        self.config.update(model_config)

    def get_config(self) -> dict[str, Any]:
        return self.config

    async def structured_output(
        self, output_model: Any, prompt: Any, system_prompt: str | None = None, **kwargs: Any
    ):
        yield {"output": self.structured}

    async def stream(
        self,
        messages: Any,
        tool_specs: list | None = None,
        system_prompt: str | None = None,
        **kwargs: Any,
    ):
        turn = self.turns.pop(0)
        self.stream_requests.append(
            {
                "messages": messages,
                "tool_specs": tool_specs,
                "system_prompt": system_prompt,
            }
        )
        yield {"messageStart": {"role": "assistant"}}
        if turn["type"] == "tool":
            yield {
                "contentBlockStart": {
                    "start": {
                        "toolUse": {
                            "name": turn["name"],
                            "toolUseId": turn.get("tool_use_id", "tool-1"),
                        }
                    }
                }
            }
            yield {
                "contentBlockDelta": {
                    "delta": {"toolUse": {"input": json.dumps(turn.get("input", {}))}}
                }
            }
            yield {"contentBlockStop": {}}
            yield {"messageStop": {"stopReason": "tool_use"}}
        else:
            yield {"contentBlockStart": {"start": {}}}
            yield {"contentBlockDelta": {"delta": {"text": turn.get("text", "")}}}
            yield {"contentBlockStop": {}}
            yield {"messageStop": {"stopReason": "end_turn"}}
        yield {
            "metadata": {
                "usage": {"inputTokens": 1, "outputTokens": 1, "totalTokens": 2},
                "metrics": {"latencyMs": 1},
            }
        }
