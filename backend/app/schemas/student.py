import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel
from app.schemas.guardian import GuardianEmbedded, GuardianRead


class StudentCreate(BaseModel):
    name: str
    first_name: str | None = None
    last_name: str | None = None
    initials: str | None = None
    accent: str | None = None
    guardians: list[GuardianEmbedded] = Field(default_factory=list)


class StudentUpdate(BaseModel):
    name: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    initials: str | None = None
    accent: str | None = None
    owner_id: uuid.UUID | None = None


class StudentRead(ORMModel):
    id: uuid.UUID
    name: str
    first_name: str | None = None
    last_name: str | None = None
    initials: str
    accent: str
    owner_id: uuid.UUID | None = None
    guardians: list[GuardianRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    created_by: uuid.UUID | None = None
    updated_by: uuid.UUID | None = None
