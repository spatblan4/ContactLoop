from uuid import UUID

from sqlalchemy.orm import Session

from app.dao import ContactEventDAO, FollowUpDAO, StudentDAO, TeacherNoteDAO
from app.schemas.outreach_plan import OutreachPlanCandidate


def _event_time(event) -> object:
    return event.call_time or event.created_at


def build_outreach_candidates(
    db: Session, owner_id: UUID | None
) -> list[OutreachPlanCandidate]:
    """Return owner-scoped, minimized facts for outreach prioritization."""
    if owner_id is None:
        return []

    students = StudentDAO(db).list(owner_id=owner_id)
    student_ids = {student.id for student in students}

    # Pick each student's most recent event explicitly instead of relying
    # on the DAO's list ordering.
    latest_events: dict = {}
    for event in ContactEventDAO(db).list(owner_id=owner_id):
        if event.student_id not in student_ids:
            continue
        current = latest_events.get(event.student_id)
        if current is None or _event_time(event) > _event_time(current):
            latest_events[event.student_id] = event

    # Keep the earliest due open follow-up per student.
    open_follow_ups: dict = {}
    for follow_up in FollowUpDAO(db).list(status="open", owner_id=owner_id):
        if follow_up.student_id not in student_ids:
            continue
        current = open_follow_ups.get(follow_up.student_id)
        if current is None or follow_up.due_at < current.due_at:
            open_follow_ups[follow_up.student_id] = follow_up

    confirmed_notes: dict[UUID, list[str]] = {}
    for note in TeacherNoteDAO(db).list(owner_id=owner_id):
        if note.student_id in student_ids and note.teacher_confirmed:
            confirmed_notes.setdefault(note.student_id, []).append(note.content)

    candidates: list[OutreachPlanCandidate] = []
    for student in students:
        event = latest_events.get(student.id)
        follow_up = open_follow_ups.get(student.id)
        candidates.append(
            OutreachPlanCandidate(
                student_id=student.id,
                student_name=student.name,
                last_contact_result=event.result if event else None,
                last_contact_at=event.call_time if event else None,
                open_follow_up_due_at=follow_up.due_at if follow_up else None,
                teacher_confirmed_notes=confirmed_notes.get(student.id, []),
            )
        )
    return candidates
