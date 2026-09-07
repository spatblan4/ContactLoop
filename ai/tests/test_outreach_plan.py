import json

from ai.outreach_plan.handler import lambda_handler


def valid_event():
    return {
        "body": json.dumps(
            {
                "candidates": [
                    {
                        "student_id": "c4b373d7-15c4-4eb8-88cd-8f6d7cbdf6fa",
                        "student_name": "Avery Student",
                        "last_contact_result": "No Answer",
                        "last_contact_at": "2026-09-06T08:00:00Z",
                        "open_follow_up_due_at": "2026-09-06T09:00:00Z",
                        "teacher_confirmed_notes": ["Parent requested a follow-up."],
                    }
                ]
            }
        ),
        "headers": {"x-contactloop-service-token": "test-token"},
    }


def test_handler_rejects_request_without_service_token(monkeypatch):
    monkeypatch.setenv("OUTREACH_PLAN_SERVICE_TOKEN", "test-token")

    response = lambda_handler(
        {"body": json.dumps({"candidates": []}), "headers": {}}, None
    )

    assert response["statusCode"] == 401


def test_handler_rejects_request_with_incorrect_service_token(monkeypatch):
    monkeypatch.setenv("OUTREACH_PLAN_SERVICE_TOKEN", "test-token")
    event = valid_event()
    event["headers"]["x-contactloop-service-token"] = "wrong-token"

    response = lambda_handler(event, None)

    assert response["statusCode"] == 401


def test_handler_rejects_invalid_candidate_body(monkeypatch):
    monkeypatch.setenv("OUTREACH_PLAN_SERVICE_TOKEN", "test-token")
    event = valid_event()
    event["body"] = json.dumps({"candidates": [{"student_name": "Missing id"}]})

    response = lambda_handler(event, None)

    assert response["statusCode"] == 400


def test_handler_returns_structured_plan(monkeypatch):
    monkeypatch.setenv("OUTREACH_PLAN_SERVICE_TOKEN", "test-token")
    monkeypatch.setattr(
        "ai.outreach_plan.handler.generate_plan",
        lambda candidates: {
            "items": [
                {
                    "student_id": candidates[0]["student_id"],
                    "priority": "high",
                    "reason": "Open follow-up is due.",
                    "suggested_next_step": "Call today.",
                }
            ]
        },
    )

    response = lambda_handler(valid_event(), None)

    assert response["statusCode"] == 200
    assert json.loads(response["body"])["items"][0]["priority"] == "high"


def test_handler_returns_no_cors_headers_for_server_to_server_calls(monkeypatch):
    monkeypatch.setenv("OUTREACH_PLAN_SERVICE_TOKEN", "test-token")
    monkeypatch.setattr("ai.outreach_plan.handler.generate_plan", lambda candidates: {"items": []})

    response = lambda_handler(valid_event(), None)

    assert not any(
        header.lower().startswith("access-control-")
        for header in response["headers"]
    )
