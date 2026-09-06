import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from app.schemas.common import ORMModel

TeacherNoteSource = Literal["typed", "voice"]


class TeacherNoteCreate(BaseModel):
    student_id: uuid.UUID
    contact_event_id: uuid.UUID | None = None
    content: str
    source: TeacherNoteSource = "typed"
    teacher_confirmed: bool = False


class TeacherNoteUpdate(BaseModel):
    content: str | None = None
    source: TeacherNoteSource | None = None
    teacher_confirmed: bool | None = None
    contact_event_id: uuid.UUID | None = None


class TeacherNoteRead(ORMModel):
    id: uuid.UUID
    student_id: uuid.UUID
    contact_event_id: uuid.UUID | None = None
    content: str
    source: str
    teacher_confirmed: bool
    created_at: datetime
    updated_at: datetime
    created_by: uuid.UUID | None = None
    updated_by: uuid.UUID | None = None
