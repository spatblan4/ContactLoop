from __future__ import annotations

import hmac
import json
import os

from pydantic import ValidationError

from .provider import OutreachPlan, OutreachPlanRequest

JSON_HEADERS = {"Content-Type": "application/json"}


def generate_plan(candidates: list[dict]) -> dict:
    """Import the Bedrock provider only when an authorized request needs it."""
    from .provider import generate_plan as provider_generate_plan

    return provider_generate_plan(candidates)


def _response(status_code: int, body: dict) -> dict:
    return {
        "statusCode": status_code,
        "headers": JSON_HEADERS,
        "body": json.dumps(body),
    }


def _service_token(event: dict) -> str | None:
    headers = event.get("headers") or {}
    if not isinstance(headers, dict):
        return None
    token = {str(key).lower(): value for key, value in headers.items()}.get(
        "x-contactloop-service-token"
    )
    return token if isinstance(token, str) else None


def lambda_handler(event, _context):
    if not isinstance(event, dict):
        return _response(401, {"error": "Unauthorized."})

    supplied_token = _service_token(event)
    expected_token = os.getenv("OUTREACH_PLAN_SERVICE_TOKEN", "")
    if not supplied_token or not hmac.compare_digest(supplied_token, expected_token):
        return _response(401, {"error": "Unauthorized."})

    try:
        body = event.get("body", {})
        if isinstance(body, str):
            body = json.loads(body)
        request = OutreachPlanRequest.model_validate(body)
    except (TypeError, json.JSONDecodeError, ValidationError):
        return _response(400, {"error": "Invalid request body."})

    try:
        result = OutreachPlan.model_validate(
            generate_plan(
                [candidate.model_dump(mode="json") for candidate in request.candidates]
            )
        )
    except Exception:
        return _response(500, {"error": "Unable to generate outreach plan."})

    return _response(200, result.model_dump(mode="json"))
