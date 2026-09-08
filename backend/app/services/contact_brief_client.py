from typing import Any

import httpx

from app.core.config import settings


class ContactBriefUnavailable(Exception):
    pass


def invoke_contact_brief(payload: dict[str, Any]) -> dict[str, Any]:
    endpoint = settings.contact_brief_endpoint
    if not endpoint:
        raise ContactBriefUnavailable("Contact Brief is not configured on this server.")

    try:
        response = httpx.post(
            f"{endpoint.rstrip('/')}/contact-brief",
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=60,
        )
    except httpx.HTTPError as exc:
        raise ContactBriefUnavailable("Unable to reach the Contact Brief service.") from exc

    if response.is_error:
        raise ContactBriefUnavailable("Contact Brief generation is temporarily unavailable.")
    try:
        body = response.json()
    except ValueError as exc:
        raise ContactBriefUnavailable("Contact Brief returned an invalid response.") from exc
    if not isinstance(body, dict):
        raise ContactBriefUnavailable("Contact Brief returned an invalid response.")
    return body
