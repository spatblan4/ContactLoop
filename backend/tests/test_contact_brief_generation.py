def test_contact_brief_generation_rejects_other_teachers_student(
    client, second_auth, make_student
):
    student = make_student(guardians=[])

    response = client.post(
        "/api/v1/ai/contact-brief/generate",
        json={
            "student_id": student["id"],
            "date_from": "2026-08-01T00:00:00Z",
            "date_to": "2026-09-08T00:00:00Z",
            "include_notes": True,
        },
        headers=second_auth["headers"],
    )

    assert response.status_code == 404


def test_contact_brief_generation_forwards_only_owned_student(
    client, make_student, monkeypatch
):
    from app.api.v1 import ai_briefs

    student = make_student(guardians=[])
    captured = {}

    def fake_invoke(payload):
        captured.update(payload)
        return {
            "provider": "aws-strands-bedrock",
            "review_status": "pending",
            "stats": {},
            "brief": {},
        }

    monkeypatch.setattr(ai_briefs, "invoke_contact_brief", fake_invoke)

    response = client.post(
        "/api/v1/ai/contact-brief/generate",
        json={
            "student_id": student["id"],
            "date_from": "2026-08-01T00:00:00Z",
            "date_to": "2026-09-08T00:00:00Z",
            "include_notes": True,
        },
    )

    assert response.status_code == 200
    assert captured["student_id"] == student["id"]
    assert captured["date_from"] == "2026-08-01T00:00:00Z"
    assert captured["date_to"] == "2026-09-08T00:00:00Z"
    assert captured["include_notes"] is True
