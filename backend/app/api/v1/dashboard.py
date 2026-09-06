from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.dao import (
    AiContactBriefDAO,
    ContactEventDAO,
    FollowUpDAO,
    StudentDAO,
    TeacherNoteDAO,
)
from app.dao.contact_event_dao import UNSUCCESSFUL_RESULTS
from app.schemas.dashboard import ContactLoopData, DashboardSummary

router = APIRouter(tags=["dashboard"])


@router.get("/data/load", response_model=ContactLoopData)
def load_contact_loop_data(db: Session = Depends(get_db)):
    students = StudentDAO(db).list()
    events = ContactEventDAO(db).list()
    follow_ups = FollowUpDAO(db).list(status="open")
    teacher_notes = TeacherNoteDAO(db).list()
    ai_briefs = [
        brief
        for brief in AiContactBriefDAO(db).list()
        if brief.status != "superseded"
    ]
    return ContactLoopData(
        students=students,
        events=events,
        follow_ups=follow_ups,
        teacher_notes=teacher_notes,
        ai_briefs=ai_briefs,
    )


@router.get("/dashboard/summary", response_model=DashboardSummary)
def dashboard_summary(
    from_: datetime | None = Query(default=None, alias="from"),
    to: datetime | None = None,
    db: Session = Depends(get_db),
):
    events = ContactEventDAO(db).list(date_from=from_, date_to=to)
    connected = sum(1 for event in events if event.result == "Connected")
    unsuccessful = sum(1 for event in events if event.result in UNSUCCESSFUL_RESULTS)
    due_limit = to or datetime.now(timezone.utc)
    follow_ups_due = sum(
        1
        for follow_up in FollowUpDAO(db).list(status="open")
        if follow_up.due_at.replace(tzinfo=None) <= due_limit.replace(tzinfo=None)
    )
    return DashboardSummary(
        call_attempts=len(events),
        connected=connected,
        unsuccessful=unsuccessful,
        follow_ups_due=follow_ups_due,
    )
