import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from app.schemas.common import ORMModel

FollowUpStatus = Literal["open", "completed", "dismissed"]


class FollowUpCreate(BaseModel):
    student_id: uuid.UUID
    guardian_id: uuid.UUID | None = None
    due_at: datetime
    status: FollowUpStatus = "open"
    contact_event_id: uuid.UUID | None = None


class FollowUpUpdate(BaseModel):
    guardian_id: uuid.UUID | None = None
    due_at: datetime | None = None
    status: FollowUpStatus | None = None
    contact_event_id: uuid.UUID | None = None


class FollowUpRead(ORMModel):
    id: uuid.UUID
    student_id: uuid.UUID
    guardian_id: uuid.UUID | None = None
    due_at: datetime
    status: str
    contact_event_id: uuid.UUID | None = None
    completed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    created_by: uuid.UUID | None = None
    updated_by: uuid.UUID | None = None
