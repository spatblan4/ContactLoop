import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel

from app.schemas.common import ORMModel

AiBriefStatus = Literal["draft", "approved", "superseded"]


class AiBriefCreate(BaseModel):
    student_id: uuid.UUID
    date_from: datetime
    date_to: datetime
    version: int = 1
    status: AiBriefStatus = "draft"
    key_topics: list[Any] = []
    parent_concerns: list[Any] = []
    recorded_resolutions: list[Any] = []
    open_items: list[Any] = []
    suggested_next_step: str | None = None


class AiBriefUpdate(BaseModel):
    status: AiBriefStatus | None = None
    key_topics: list[Any] | None = None
    parent_concerns: list[Any] | None = None
    recorded_resolutions: list[Any] | None = None
    open_items: list[Any] | None = None
    suggested_next_step: str | None = None


class AiBriefRead(ORMModel):
    id: uuid.UUID
    student_id: uuid.UUID
    date_from: datetime
    date_to: datetime
    version: int
    status: str
    key_topics: list[Any] = []
    parent_concerns: list[Any] = []
    recorded_resolutions: list[Any] = []
    open_items: list[Any] = []
    suggested_next_step: str | None = None
    generated_at: datetime
    approved_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    created_by: uuid.UUID | None = None
    updated_by: uuid.UUID | None = None
