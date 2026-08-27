from __future__ import annotations

import os
from typing import Any

from pydantic import BaseModel
from strands import Agent
from strands.models import BedrockModel

from .schema import ContactBrief, ContactStats
from .supabase_reader import SupabaseContactReader
from .tools import build_contact_tools


SYSTEM_PROMPT = """You create a Contact Brief for a special education teacher.

You must call the available tools before writing the brief. Use only teacher-approved
notes, selected topics, and open follow-up records returned by the tools.
For Connected calls, treat discussed_topics as the topics actually discussed.
For No Answer, Busy, or Failed calls, use planned_topic only to describe an
unsuccessful outreach attempt; never say that an unsuccessful call discussed anything.
Never invent a concern, request, resolution, topic, or follow-up. If evidence is
missing, return an empty list for that field. Do not calculate any numbers; counts
are authoritative Supabase values and are returned separately by the service.
Do not make legal, compliance, medical, or educational judgments. Do not mention
phone numbers, provider IDs, recordings, transcripts, or internal system details.
Return only the requested structured ContactBrief fields.
"""


class ContactBriefResponse(BaseModel):
    provider: str
    review_status: str
    stats: ContactStats
    brief: ContactBrief


class AwsStrandsContactBriefProvider:
    name = "aws-strands-bedrock"

    def __init__(self, reader: SupabaseContactReader | None = None, model_id: str | None = None, region: str | None = None):
        self.reader = reader or SupabaseContactReader(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_ROLE_KEY"])
        self.model_id = model_id or os.getenv("BEDROCK_MODEL_ID", "us.anthropic.claude-sonnet-4-6")
        self.region = region or os.getenv("AWS_REGION", "us-east-1")

    def generate(self, *, student_id: str, date_from: str, date_to: str, include_notes: bool = True) -> dict[str, Any]:
        stats = ContactStats.model_validate(self.reader.get_stats(student_id, date_from, date_to))
        agent = Agent(
            model=BedrockModel(model_id=self.model_id, region_name=self.region, temperature=0.2),
            tools=build_contact_tools(self.reader, include_notes=include_notes),
            system_prompt=SYSTEM_PROMPT,
        )
        prompt = (
            f"Generate a structured ContactBrief for student_id={student_id}. "
            f"Date range: {date_from} through {date_to}. "
            f"include_teacher_notes: {include_notes}. "
            "Call all three tools. Use notes/topics for narrative evidence and open "
            "follow-ups for unresolved items. Do not output counts or numbers in "
            "narrative fields; the service attaches authoritative stats separately."
        )
        result = agent(prompt, structured_output_model=ContactBrief)
        return ContactBriefResponse(
            provider=self.name,
            review_status="pending",
            stats=stats,
            brief=result.structured_output,
        ).model_dump()
