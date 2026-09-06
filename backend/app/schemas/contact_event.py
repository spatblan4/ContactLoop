import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from app.schemas.common import ORMModel

ContactEventResult = Literal["Connected", "No Answer", "Busy", "Failed"]


class ContactEventCreate(BaseModel):
    student_id: uuid.UUID
    guardian_id: uuid.UUID | None = None
    result: ContactEventResult
    duration_seconds: int | None = None
    topic: str | None = None
    planned_topic: str | None = None
    discussed_topics: list[str] = []
    teacher_note: str | None = None
    call_time: datetime | None = None
    started_at: datetime | None = None
    ended_at: datetime | None = None
    follow_up_id: uuid.UUID | None = None
    follow_up_due_at: datetime | None = None


class ContactEventUpdate(BaseModel):
    guardian_id: uuid.UUID | None = None
    result: ContactEventResult | None = None
    duration_seconds: int | None = None
    topic: str | None = None
    planned_topic: str | None = None
    discussed_topics: list[str] | None = None
    teacher_note: str | None = None
    call_time: datetime | None = None
    started_at: datetime | None = None
    ended_at: datetime | None = None
    follow_up_id: uuid.UUID | None = None
    follow_up_due_at: datetime | None = None


class ContactEventRead(ORMModel):
    id: uuid.UUID
    student_id: uuid.UUID
    guardian_id: uuid.UUID | None = None
    call_time: datetime
    duration_seconds: int | None = None
    result: str
    attempt_number: int
    topic: str | None = None
    planned_topic: str | None = None
    discussed_topics: list[str] = []
    teacher_note: str | None = None
    follow_up_id: uuid.UUID | None = None
    provider: str | None = None
    provider_call_id: str | None = None
    provider_status: str | None = None
    started_at: datetime | None = None
    ended_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    created_by: uuid.UUID | None = None
    updated_by: uuid.UUID | None = None
