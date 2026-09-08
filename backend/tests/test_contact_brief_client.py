import httpx


def test_contact_brief_client_posts_only_allowed_payload(monkeypatch):
    from app.core.config import settings
    from app.services import contact_brief_client

    captured = {}

    def fake_post(url, **kwargs):
        captured.update(url=url, **kwargs)
        return httpx.Response(
            200,
            json={"provider": "aws-strands-bedrock", "brief": {}},
        )

    monkeypatch.setattr(contact_brief_client.httpx, "post", fake_post)
    monkeypatch.setattr(settings, "contact_brief_endpoint", "https://lambda.example.test")

    result = contact_brief_client.invoke_contact_brief(
        {
            "student_id": "student-1",
            "date_from": "2026-08-01T00:00:00Z",
            "date_to": "2026-09-08T00:00:00Z",
            "include_notes": True,
        }
    )

    assert result["provider"] == "aws-strands-bedrock"
    assert captured["url"] == "https://lambda.example.test/contact-brief"
    assert captured["json"] == {
        "student_id": "student-1",
        "date_from": "2026-08-01T00:00:00Z",
        "date_to": "2026-09-08T00:00:00Z",
        "include_notes": True,
    }
