"""Owner-scoped, read-only Strands tools over the ContactLoop database.

Every tool closes over the requesting teacher's database session and owner id,
and per-student tools verify ownership through ``require_owned_student`` before
returning any data, so the agent can never read another teacher's students.
Returned payloads are minimized: no phone numbers, no credentials.
"""

from typing import Any

from sqlalchemy.orm import Session as DbSession

from app.dao import ContactEventDAO, FollowUpDAO, TeacherNoteDAO
from app.services.ownership import require_owned_student

MAX_HISTORY_EVENTS = 20
MAX_NOTES = 10


def build_outreach_tools(
    db: DbSession, owner_id: Any, candidates: list[dict]
) -> list[tuple[Any, str]]:
    """Build the read-only tool set for the outreach agents.

    Returns a list of ``(tool, name)`` pairs so callers can register the tools
    and keep the guard whitelist in sync from the same source.
    """
    from strands import tool

    @tool
    def get_outreach_candidates() -> list[dict]:
        """Get the teacher-authorized candidate facts for today's outreach plan."""
        return candidates

    @tool
    def get_contact_history(student_id: str) -> list[dict]:
        """Get the recent contact history for one of your students.

        Args:
            student_id: UUID of the student, as shown in the outreach candidates.
        """
        require_owned_student(db, _uuid(student_id), owner_id)
        events = ContactEventDAO(db).list(
            student_id=_uuid(student_id), owner_id=owner_id
        )
        rows = [
            {
                "result": event.result,
                "call_time": _iso(event.call_time or event.created_at),
                "attempt_number": event.attempt_number,
            }
            for event in events
        ]
        return rows[:MAX_HISTORY_EVENTS]

    @tool
    def get_open_follow_ups() -> list[dict]:
        """Get the currently open follow-ups for your students."""
        follow_ups = FollowUpDAO(db).list(status="open", owner_id=owner_id)
        return [
            {
                "student_id": str(follow_up.student_id),
                "due_at": _iso(follow_up.due_at),
                "status": follow_up.status,
            }
            for follow_up in follow_ups
        ][:MAX_HISTORY_EVENTS]

    @tool
    def get_teacher_notes(student_id: str) -> list[dict]:
        """Get your confirmed teacher notes for one of your students.

        Args:
            student_id: UUID of the student, as shown in the outreach candidates.
        """
        require_owned_student(db, _uuid(student_id), owner_id)
        notes = TeacherNoteDAO(db).list(student_id=_uuid(student_id), owner_id=owner_id)
        rows = [
            {
                "content": note.content,
                "source": note.source,
                "teacher_confirmed": note.teacher_confirmed,
            }
            for note in notes
            if note.teacher_confirmed
        ]
        return rows[:MAX_NOTES]

    return [
        (get_outreach_candidates, "get_outreach_candidates"),
        (get_contact_history, "get_contact_history"),
        (get_open_follow_ups, "get_open_follow_ups"),
        (get_teacher_notes, "get_teacher_notes"),
    ]


def _uuid(value: str):
    import uuid

    return uuid.UUID(str(value))


def _iso(value) -> str | None:
    if value is None:
        return None
    try:
        return value.isoformat()
    except AttributeError:
        return str(value)
