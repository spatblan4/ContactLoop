from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.dao import ContactEventDAO, FollowUpDAO, StudentDAO, TeacherNoteDAO
from app.schemas.outreach_plan import OutreachPlanCandidate


def build_outreach_candidates(
    db: Session, owner_id: UUID | None, now: datetime
) -> list[dict]:
    """Return owner-scoped, minimized facts for outreach prioritization."""
    del now
    students = StudentDAO(db).list(owner_id=owner_id)
    student_ids = {student.id for student in students}
    latest_events = {
        event.student_id: event
        for event in ContactEventDAO(db).list(owner_id=owner_id)
        if event.student_id in student_ids
    }
    open_follow_ups = {
        follow_up.student_id: follow_up
        for follow_up in FollowUpDAO(db).list(status="open", owner_id=owner_id)
        if follow_up.student_id in student_ids
    }
    confirmed_notes: dict[UUID, list[str]] = {}
    for note in TeacherNoteDAO(db).list(owner_id=owner_id):
        if note.student_id in student_ids and note.teacher_confirmed:
            confirmed_notes.setdefault(note.student_id, []).append(note.content)

    return [
        OutreachPlanCandidate(
            student_id=student.id,
            student_name=student.name,
            last_contact_result=latest_events.get(student.id).result
            if student.id in latest_events
            else None,
            last_contact_at=latest_events.get(student.id).call_time
            if student.id in latest_events
            else None,
            open_follow_up_due_at=open_follow_ups.get(student.id).due_at
            if student.id in open_follow_ups
            else None,
            teacher_confirmed_notes=confirmed_notes.get(student.id, []),
        ).model_dump(mode="json")
        for student in students
    ]
