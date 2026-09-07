from typing import Any
import httpx
from app.core.config import settings
from app.schemas.outreach_plan import OutreachPlanResponse


class OutreachAgentUnavailable(Exception):
    pass


def invoke_outreach_agent(candidates: list[dict[str, Any]]) -> OutreachPlanResponse:
    endpoint = (settings.outreach_plan_endpoint or "").rstrip("/")
    token = settings.outreach_plan_service_token
    if not endpoint or not token:
        raise OutreachAgentUnavailable()
    try:
        response = httpx.post(endpoint, json={"candidates": candidates}, headers={"X-ContactLoop-Service-Token": token}, timeout=30.0)
        response.raise_for_status()
        return OutreachPlanResponse.model_validate(response.json())
    except (httpx.HTTPError, ValueError):
        raise OutreachAgentUnavailable() from None
