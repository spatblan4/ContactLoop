from __future__ import annotations

import os
from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class OutreachPlanCandidate(BaseModel):
    """Minimized, owner-authorized context provided by the FastAPI service."""

    model_config = ConfigDict(extra="forbid")

    student_id: UUID
    student_name: str
    last_contact_result: str | None = None
    last_contact_at: datetime | None = None
    open_follow_up_due_at: datetime | None = None
    teacher_confirmed_notes: list[str] = Field(default_factory=list)


class OutreachPlanRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    candidates: list[OutreachPlanCandidate]


class OutreachPlanItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    student_id: UUID
    priority: Literal["high", "medium", "low"]
    reason: str
    suggested_next_step: str


class OutreachPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[OutreachPlanItem]


SYSTEM_PROMPT = """You prioritize parent outreach using only the candidate facts supplied by tools.
Return one item per recommended student. Never invent student facts. Never include phone numbers.
Use high priority only for overdue or open follow-ups; otherwise use medium or low.
Return only the requested structured OutreachPlan fields."""


def get_candidates_tool(candidates: list[dict]):
    """Create the sole Agent tool, exposing only the authorized candidate facts."""
    from strands import tool

    @tool
    def get_outreach_candidates() -> list[dict]:
        """Get the authorized candidate facts for today's outreach plan."""
        return candidates

    return get_outreach_candidates


def generate_plan(candidates: list[dict]) -> dict:
    """Generate advisory outreach recommendations from supplied candidate facts."""
    from strands import Agent
    from strands.models import BedrockModel

    agent = Agent(
        model=BedrockModel(
            model_id=os.environ["BEDROCK_MODEL_ID"],
            region_name=os.environ.get("AWS_REGION", "us-east-1"),
            temperature=0.2,
        ),
        tools=[get_candidates_tool(candidates)],
        system_prompt=SYSTEM_PROMPT,
    )
    result = agent("Create today's outreach plan.", structured_output_model=OutreachPlan)
    structured_output = getattr(result, "structured_output", result)
    return OutreachPlan.model_validate(structured_output).model_dump(mode="json")
