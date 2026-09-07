import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class AuthRegister(BaseModel):
    email: str = Field(max_length=320)
    password: str = Field(min_length=6, max_length=128)
    name: str | None = None


class AuthLogin(BaseModel):
    email: str
    password: str


class AuthUser(BaseModel):
    id: uuid.UUID
    email: str
    name: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AuthResponse(BaseModel):
    user: AuthUser
    token: str
