import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id, get_db
from app.dao import ContactEventDAO
from app.schemas.contact_event import (
    ContactEventCreate,
    ContactEventRead,
    ContactEventUpdate,
)

router = APIRouter(prefix="/contact-events", tags=["contact-events"])


@router.get("", response_model=list[ContactEventRead])
def list_contact_events(
    student_id: uuid.UUID | None = None,
    from_: datetime | None = Query(default=None, alias="from"),
    to: datetime | None = None,
    result: str | None = None,
    db: Session = Depends(get_db),
    user_id: uuid.UUID | None = Depends(get_current_user_id),
):
    return ContactEventDAO(db).list(
        student_id=student_id, date_from=from_, date_to=to, result=result, owner_id=user_id
    )


@router.post("", response_model=ContactEventRead, status_code=201)
def create_contact_event(
    payload: ContactEventCreate,
    db: Session = Depends(get_db),
    user_id: uuid.UUID | None = Depends(get_current_user_id),
):
    data = {
        key: value
        for key, value in payload.model_dump(
            exclude={"follow_up_due_at"}
        ).items()
        if value is not None
    }
    if payload.ended_at is None:
        data["ended_at"] = payload.call_time or datetime.now(timezone.utc)
    event = ContactEventDAO(db).create(
        data, actor_id=user_id, follow_up_due_at=payload.follow_up_due_at
    )
    db.commit()
    return event


@router.get("/{event_id}", response_model=ContactEventRead)
def get_contact_event(event_id: uuid.UUID, db: Session = Depends(get_db)):
    return ContactEventDAO(db).require(event_id)


@router.patch("/{event_id}", response_model=ContactEventRead)
def update_contact_event(
    event_id: uuid.UUID,
    payload: ContactEventUpdate,
    db: Session = Depends(get_db),
    user_id: uuid.UUID | None = Depends(get_current_user_id),
):
    data = payload.model_dump(
        exclude={"follow_up_due_at", "attempt_number"}, exclude_unset=True
    )
    event = ContactEventDAO(db).update(
        event_id, data, actor_id=user_id, follow_up_due_at=payload.follow_up_due_at
    )
    db.commit()
    return event


@router.delete("/{event_id}", status_code=204)
def delete_contact_event(
    event_id: uuid.UUID,
    db: Session = Depends(get_db),
    user_id: uuid.UUID | None = Depends(get_current_user_id),
):
    ContactEventDAO(db).soft_delete(event_id, actor_id=user_id)
    db.commit()
