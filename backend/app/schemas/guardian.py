import uuid
from datetime import datetime

from pydantic import BaseModel

from app.schemas.common import ORMModel


class GuardianBase(BaseModel):
    name: str
    relation: str
    phone: str | None = None
    email: str | None = None
    preferred_contact_method: str | None = None


class GuardianEmbedded(GuardianBase):
    pass


class GuardianCreate(GuardianBase):
    student_id: uuid.UUID


class GuardianUpdate(BaseModel):
    name: str | None = None
    relation: str | None = None
    phone: str | None = None
    email: str | None = None
    preferred_contact_method: str | None = None


class GuardianRead(ORMModel):
    id: uuid.UUID
    student_id: uuid.UUID
    name: str
    relation: str
    phone: str | None = None
    email: str | None = None
    preferred_contact_method: str | None = None
    created_at: datetime
    updated_at: datetime
    created_by: uuid.UUID | None = None
    updated_by: uuid.UUID | None = None
