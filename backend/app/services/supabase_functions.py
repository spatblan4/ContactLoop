import uuid

import httpx

from app.core.config import settings


class SupabaseFunctionError(Exception):
    pass


def _invoke(function_name: str, payload: dict[str, str | None]) -> dict:
    if not settings.supabase_url or not settings.supabase_secret_key:
        raise SupabaseFunctionError("Twilio calling is not configured on this server.")

    try:
        response = httpx.post(
            f"{settings.supabase_url.rstrip('/')}/functions/v1/{function_name}",
            headers={
                "apikey": settings.supabase_secret_key,
                "Authorization": f"Bearer {settings.supabase_secret_key}",
            },
            json=payload,
            timeout=settings.supabase_function_timeout_seconds,
        )
    except httpx.HTTPError as exc:
        raise SupabaseFunctionError("Unable to reach the calling service.") from exc

    try:
        body = response.json()
    except ValueError:
        body = {}
    if response.is_error:
        raise SupabaseFunctionError("The calling service rejected this request.")
    if not isinstance(body, dict):
        raise SupabaseFunctionError("The calling service returned an invalid response.")
    return body


def invoke_start_call(student_id: uuid.UUID, planned_topic: str | None) -> dict:
    return _invoke(
        "start-call",
        {"studentId": str(student_id), "plannedTopic": planned_topic},
    )


def invoke_call_status_sync(event_id: uuid.UUID) -> dict:
    return _invoke("sync-call-status", {"eventId": str(event_id)})
