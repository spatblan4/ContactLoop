"""Local-only Strands/Bedrock implementation for teacher outreach advice."""

import logging
from typing import Any

from app.core.config import settings
from app.schemas.outreach_plan import OutreachPlanAgentOutput
from app.services.agent_telemetry import configure_strands_telemetry
from app.services.outreach_agent_hooks import ReadOnlyToolGuard

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You prioritize parent outreach using only the supplied candidate facts.
Return only recommendations supported by those facts. Never invent student facts.
Never include phone numbers. Use high priority only for an overdue or open follow-up;
otherwise use medium or low. This is teacher-reviewed advice only."""

READ_ONLY_TOOLS = ("get_outreach_candidates",)

# Strands implements structured output by registering a tool named after the
# pydantic model class, so the guard whitelist must include it.
STRUCTURED_OUTPUT_TOOL_NAME = OutreachPlanAgentOutput.__name__


def _build_bedrock_model() -> "Any":
    from strands.models import BedrockModel

    bedrock_config: dict[str, Any] = {
        "model_id": settings.bedrock_model_id,
        "temperature": settings.bedrock_temperature,
    }
    if settings.bedrock_guardrail_id:
        bedrock_config.update(
            guardrail_id=settings.bedrock_guardrail_id,
            guardrail_version=settings.bedrock_guardrail_version,
            guardrail_trace="enabled",
        )
    return BedrockModel(region_name=settings.aws_region, **bedrock_config)


def build_outreach_agent(
    candidates: list[dict[str, Any]],
    model: Any = None,
    owner_id: Any = None,
) -> Any:
    """Construct the Strands outreach agent.

    ``model`` defaults to the Bedrock model from settings and exists so tests
    can drive the real agent loop with a scripted fake model.
    """
    from strands import Agent, tool

    @tool
    def get_outreach_candidates() -> list[dict[str, Any]]:
        """Get the teacher-authorized candidate facts for today's outreach plan."""
        return candidates

    trace_attributes = {"contactloop.agent": "outreach_plan"}
    if owner_id is not None:
        trace_attributes["contactloop.owner_id"] = str(owner_id)

    return Agent(
        model=model if model is not None else _build_bedrock_model(),
        tools=[get_outreach_candidates],
        system_prompt=SYSTEM_PROMPT,
        hooks=[
            ReadOnlyToolGuard([*READ_ONLY_TOOLS, STRUCTURED_OUTPUT_TOOL_NAME])
        ],
        trace_attributes=trace_attributes,
    )


def generate_plan(
    candidates: list[dict[str, Any]], owner_id: Any = None
) -> dict[str, Any]:
    """Run the real Bedrock Agent locally with owner-authorized candidate facts."""
    if not settings.bedrock_model_id:
        raise RuntimeError("Bedrock model is not configured.")
    if not settings.aws_region:
        raise RuntimeError("Bedrock region is not configured; set AWS_REGION.")

    try:
        from strands import Agent, tool  # noqa: F401
    except ImportError as exc:
        raise RuntimeError(
            "Strands agent dependencies are not installed. "
            "Install backend/requirements-bedrock.txt."
        ) from exc

    configure_strands_telemetry()
    agent = build_outreach_agent(candidates, owner_id=owner_id)
    result = agent(
        "Create today's outreach plan.",
        structured_output_model=OutreachPlanAgentOutput,
    )
    structured_output = getattr(result, "structured_output", result)
    return OutreachPlanAgentOutput.model_validate(structured_output).model_dump(mode="json")
