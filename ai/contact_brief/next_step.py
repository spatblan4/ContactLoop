from __future__ import annotations

from datetime import datetime
from typing import Any


DEFAULT_NEXT_STEP = "No suggested next step recorded."
_EMPTY_SUGGESTIONS = {"", DEFAULT_NEXT_STEP.casefold(), "no suggestion.", "none."}


def _parse_due_at(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None


def _format_due_date(value: datetime) -> str:
    return f"{value.strftime('%A, %B')} {value.day}, {value.year}"


def grounded_suggested_next_step(current: str | None, follow_ups: list[dict[str, Any]]) -> str:
    """Fill a missing model suggestion from the earliest recorded open follow-up."""

    suggestion = (current or "").strip()
    if suggestion.casefold() not in _EMPTY_SUGGESTIONS:
        return suggestion

    dated_follow_ups = [
        due_at
        for follow_up in follow_ups
        if follow_up.get("status") == "open" and (due_at := _parse_due_at(follow_up.get("due_at")))
    ]
    if dated_follow_ups:
        earliest = min(dated_follow_ups)
        return f"Follow up with the parent on {_format_due_date(earliest)}."

    if any(follow_up.get("status") == "open" for follow_up in follow_ups):
        return "Complete the open parent follow-up."

    return DEFAULT_NEXT_STEP
