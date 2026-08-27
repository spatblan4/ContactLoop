from __future__ import annotations

from typing import Protocol


class ContactBriefProvider(Protocol):
    name: str

    def generate(self, *, student_id: str, date_from: str, date_to: str, include_notes: bool = True) -> dict:
        """Return authoritative stats plus a review-pending narrative brief."""
