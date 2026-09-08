from datetime import datetime, timezone
from typing import Any

from app.core.config import settings
from app.schemas.outreach_plan import OutreachPlanResponse
from app.services.outreach_plan_agent import generate_plan


class OutreachAgentUnavailable(Exception):
    pass


def invoke_outreach_agent(candidates: list[dict[str, Any]]) -> OutreachPlanResponse:
    if not settings.bedrock_model_id:
        raise OutreachAgentUnavailable()
    try:
        authorized_student_ids = {
            str(candidate["student_id"]) for candidate in candidates
        }
        payload = generate_plan(candidates)
        response = OutreachPlanResponse(
            generated_at=datetime.now(timezone.utc), source="agent", items=payload["items"]
        )
        if any(
            str(item.student_id) not in authorized_student_ids for item in response.items
        ):
            raise ValueError("Agent returned a student outside the authorized candidates.")
        return response
    except Exception:
        raise OutreachAgentUnavailable() from None
