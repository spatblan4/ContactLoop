from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class OutreachPlanCandidate(BaseModel):
    student_id: UUID
    student_name: str
    last_contact_result: str | None = None
    last_contact_at: datetime | None = None
    open_follow_up_due_at: datetime | None = None
    teacher_confirmed_notes: list[str] = Field(default_factory=list)


class OutreachPlanItem(BaseModel):
    student_id: UUID
    priority: Literal["high", "medium", "low"]
    reason: str
    suggested_next_step: str


class OutreachPlanAgentOutput(BaseModel):
    items: list[OutreachPlanItem]


class OutreachPlanResponse(BaseModel):
    generated_at: datetime
    source: Literal["agent", "demo"]
    items: list[OutreachPlanItem]
