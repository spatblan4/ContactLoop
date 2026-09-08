import uuid

import httpx
import pytest

from app.core.config import Settings, settings
from app.services.supabase_functions import invoke_start_call


def test_settings_expose_server_only_supabase_function_configuration():
    settings = Settings(
        supabase_url="https://project.supabase.co",
        supabase_secret_key="server-only-key",
    )

    assert settings.supabase_url == "https://project.supabase.co"
    assert settings.supabase_secret_key == "server-only-key"


def test_start_call_function_receives_only_student_and_planned_topic(monkeypatch):
    captured = {}

    def fake_post(url, **kwargs):
        captured["url"] = url
        captured.update(kwargs)
        return httpx.Response(
            200,
            json={"eventId": "event-1"},
            request=httpx.Request("POST", url),
        )

    monkeypatch.setattr(settings, "supabase_url", "https://project.supabase.co")
    monkeypatch.setattr(settings, "supabase_secret_key", "server-only-key")
    monkeypatch.setattr(httpx, "post", fake_post)

    result = invoke_start_call(
        uuid.UUID("11111111-1111-4111-8111-111111111111"), "Behavior"
    )

    assert result == {"eventId": "event-1"}
    assert captured["url"] == "https://project.supabase.co/functions/v1/start-call"
    assert captured["json"] == {
        "studentId": "11111111-1111-4111-8111-111111111111",
        "plannedTopic": "Behavior",
    }


def test_calling_service_rejection_hides_raw_upstream_error(monkeypatch):
    from app.services.supabase_functions import SupabaseFunctionError

    def fake_post(url, **_kwargs):
        return httpx.Response(
            502,
            json={"error": "raw database or Twilio provider detail"},
            request=httpx.Request("POST", url),
        )

    monkeypatch.setattr(settings, "supabase_url", "https://project.supabase.co")
    monkeypatch.setattr(settings, "supabase_secret_key", "server-only-key")
    monkeypatch.setattr(httpx, "post", fake_post)

    with pytest.raises(SupabaseFunctionError) as exc_info:
        invoke_start_call(
            uuid.UUID("11111111-1111-4111-8111-111111111111"), "Behavior"
        )

    assert str(exc_info.value) == "The calling service rejected this request."
    assert "raw database" not in str(exc_info.value)
