from typing import List

from pydantic import BaseModel, Field


class ContactStats(BaseModel):
    """Authoritative counts calculated by the Supabase RPC."""

    total_attempts: int = Field(ge=0)
    successful_conversations: int = Field(ge=0)
    no_answer: int = Field(ge=0)
    busy: int = Field(ge=0)
    failed: int = Field(ge=0)
    last_successful_contact: str | None = None
    open_follow_ups: int = Field(ge=0)


class ContactBrief(BaseModel):
    """Narrative fields grounded only in records returned by the tools."""

    key_topics: List[str] = Field(default_factory=list)
    parent_concerns: List[str] = Field(default_factory=list)
    recorded_resolutions: List[str] = Field(default_factory=list)
    open_items: List[str] = Field(default_factory=list)
    suggested_next_step: str = "No suggested next step recorded."
