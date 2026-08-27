from __future__ import annotations

from typing import Any

import httpx


class SupabaseContactReader:
    """Read-only Supabase access for the AI tools."""

    def __init__(self, url: str, key: str, timeout: float = 10.0):
        self.base_url = url.rstrip("/")
        self.headers = {"apikey": key, "Authorization": f"Bearer {key}"}
        self.timeout = timeout

    def _get(self, table: str, params: dict[str, str]) -> list[dict[str, Any]]:
        response = httpx.get(f"{self.base_url}/rest/v1/{table}", headers=self.headers, params=params, timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def get_stats(self, student_id: str, date_from: str, date_to: str) -> dict[str, Any]:
        response = httpx.post(
            f"{self.base_url}/rest/v1/rpc/get_contact_stats",
            headers={**self.headers, "Content-Type": "application/json"},
            json={"p_student_id": student_id, "p_from": date_from, "p_to": date_to},
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()

    def get_notes_and_topics(self, student_id: str, date_from: str, date_to: str, include_notes: bool = True) -> list[dict[str, Any]]:
        events = self._get("contact_events", {
            "select": "id,call_time,result,topic,planned_topic,discussed_topics,teacher_note" if include_notes else "id,call_time,result,topic,planned_topic,discussed_topics",
            "student_id": f"eq.{student_id}",
            "call_time": f"gte.{date_from}",
            "and": f"(call_time.lt.{date_to})",
            "order": "call_time.desc",
        })
        if not include_notes:
            return events

        teacher_notes = self._get("teacher_notes", {
            "select": "id,created_at,content,source,teacher_confirmed",
            "student_id": f"eq.{student_id}",
            "created_at": f"gte.{date_from}",
            "and": f"(created_at.lt.{date_to})",
            "teacher_confirmed": "eq.true",
            "order": "created_at.desc",
        })
        return [*events, *[
            {
                "id": note["id"],
                "call_time": note["created_at"],
                "result": "Teacher note",
                "planned_topic": None,
                "discussed_topics": [],
                "teacher_note": note["content"],
                "note_source": note.get("source", "typed"),
            }
            for note in teacher_notes
        ]]

    def get_open_follow_ups(self, student_id: str) -> list[dict[str, Any]]:
        return self._get("follow_ups", {
            "select": "id,due_at,status,contact_event_id",
            "student_id": f"eq.{student_id}",
            "status": "eq.open",
            "order": "due_at.asc",
        })
