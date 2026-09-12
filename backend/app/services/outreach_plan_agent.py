"""Local-only Strands/Bedrock implementation for teacher outreach advice."""

from typing import Any

from app.core.config import settings
from app.schemas.outreach_plan import OutreachPlanAgentOutput

SYSTEM_PROMPT = """You prioritize parent outreach using only the supplied candidate facts.
Return only recommendations supported by those facts. Never invent student facts.
Never include phone numbers. Use high priority only for an overdue or open follow-up;
otherwise use medium or low. This is teacher-reviewed advice only."""


def generate_plan(candidates: list[dict[str, Any]]) -> dict[str, Any]:
    """Run the real Bedrock Agent locally with owner-authorized candidate facts."""
    if not settings.bedrock_model_id:
        raise RuntimeError("Bedrock model is not configured.")
    if not settings.aws_region:
        raise RuntimeError("Bedrock region is not configured; set AWS_REGION.")

    try:
        from strands import Agent, tool
        from strands.models import BedrockModel
    except ImportError as exc:
        raise RuntimeError(
            "Strands agent dependencies are not installed. "
            "Install backend/requirements-bedrock.txt."
        ) from exc

    @tool
    def get_outreach_candidates() -> list[dict[str, Any]]:
        """Get the teacher-authorized candidate facts for today's outreach plan."""
        return candidates

    agent = Agent(
        model=BedrockModel(
            model_id=settings.bedrock_model_id,
            region_name=settings.aws_region,
            temperature=settings.bedrock_temperature,
        ),
        tools=[get_outreach_candidates],
        system_prompt=SYSTEM_PROMPT,
    )
    result = agent(
        "Create today's outreach plan.",
        structured_output_model=OutreachPlanAgentOutput,
    )
    structured_output = getattr(result, "structured_output", result)
    return OutreachPlanAgentOutput.model_validate(structured_output).model_dump(mode="json")
