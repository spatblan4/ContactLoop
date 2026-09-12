from app.api.v1.voice import voice_dir


def _request_upload(client, student_id, content_type="audio/webm"):
    response = client.post(
        "/api/v1/voice/uploads",
        json={"student_id": student_id, "content_type": content_type},
    )
    assert response.status_code == 200
    return response.json()


def test_voice_stub_flow_upload_put_and_transcription(client, make_student):
    student = make_student(guardians=[])

    body = _request_upload(client, student["id"])
    object_key = body["object_key"]
    assert object_key
    assert body["upload_url"] == f"/api/v1/voice/files/{object_key}"

    voice_bytes = b"fake-webm-audio-bytes"
    put_response = client.put(body["upload_url"], content=voice_bytes)
    assert put_response.status_code == 204
    saved = voice_dir() / object_key
    assert saved.exists()
    assert saved.read_bytes() == voice_bytes

    response = client.post(
        "/api/v1/voice/transcriptions",
        json={"student_id": student["id"], "object_key": object_key},
    )
    assert response.status_code == 200
    job_id = response.json()["job_id"]
    assert job_id

    response = client.get(f"/api/v1/voice/transcriptions/{job_id}")
    assert response.status_code == 200
    assert response.json() == {
        "status": "completed",
        "transcript": "(Voice note saved locally. Transcription is not configured.)",
    }
    saved.unlink(missing_ok=True)


def test_voice_upload_rejects_invalid_object_key(client):
    response = client.put("/api/v1/voice/files/bad key!", content=b"x")
    assert response.status_code == 400


def test_voice_upload_rejects_unknown_object_key(client):
    response = client.put("/api/v1/voice/files/" + "a" * 32, content=b"x")
    assert response.status_code == 404


def test_voice_upload_rejects_another_users_object_key(
    client, second_auth, make_student
):
    student = make_student(guardians=[])
    body = _request_upload(client, student["id"])

    response = client.put(body["upload_url"], content=b"x", headers=second_auth["headers"])

    assert response.status_code == 404
    assert not (voice_dir() / body["object_key"]).exists()


def test_voice_upload_rejects_oversized_file(client, make_student, monkeypatch):
    student = make_student(guardians=[])
    body = _request_upload(client, student["id"])

    monkeypatch.setattr(
        "app.api.v1.voice.settings",
        type("Settings", (), {"voice_max_upload_bytes": 4, "voice_notes_dir": None}),
    )

    response = client.put(body["upload_url"], content=b"x" * 16)

    assert response.status_code == 413
    assert not (voice_dir() / body["object_key"]).exists()


def test_voice_transcription_rejects_another_users_object_key(
    client, second_auth, make_student
):
    student = make_student(guardians=[])
    other = make_student(guardians=[], headers=second_auth["headers"])
    body = _request_upload(client, student["id"])

    response = client.post(
        "/api/v1/voice/transcriptions",
        json={"student_id": other["id"], "object_key": body["object_key"]},
        headers=second_auth["headers"],
    )

    assert response.status_code == 404


def test_voice_transcription_requires_uploaded_file(client, make_student):
    student = make_student(guardians=[])
    body = _request_upload(client, student["id"])

    response = client.post(
        "/api/v1/voice/transcriptions",
        json={"student_id": student["id"], "object_key": body["object_key"]},
    )

    assert response.status_code == 404


def test_voice_transcription_job_creates_unconfirmed_teacher_note_draft(
    client, make_student, monkeypatch
):
    student = make_student(guardians=[])
    body = _request_upload(client, student["id"])
    voice_bytes = b"fake-webm-audio-bytes"
    assert client.put(body["upload_url"], content=voice_bytes).status_code == 204

    monkeypatch.setattr(
        "app.services.voice_transcription.transcribe_enabled",
        lambda: True,
    )
    monkeypatch.setattr(
        "app.services.voice_transcription._transcribe_file",
        lambda file_path: "Parent asked about homework schedule.",
    )

    from app.services import voice_transcription

    original_finalize = voice_transcription._finalize_draft
    completed = {}

    def fake_finalize(job_id, user_id, student_id, transcript):
        completed["args"] = (user_id, student_id, transcript)
        monkeypatch.setattr(
            "app.services.note_drafts.draft_note_content",
            lambda facts: "Summary: parent asked about homework.",
        )
        original_finalize(job_id, user_id, student_id, transcript)

    monkeypatch.setattr(voice_transcription, "_finalize_draft", fake_finalize)

    started = client.post(
        "/api/v1/voice/transcriptions",
        json={"student_id": student["id"], "object_key": body["object_key"]},
    )
    assert started.status_code == 200
    job_id = started.json()["job_id"]

    import time

    for _ in range(50):
        if voice_transcription.get_job(job_id).get("status") != "processing":
            break
        time.sleep(0.05)

    job = voice_transcription.get_job(job_id)
    assert job["status"] == "completed"
    assert job["transcript"] == "Parent asked about homework schedule."
    user_id, student_id, _transcript = completed["args"]

    notes = client.get(
        "/api/v1/teacher-notes", params={"student_id": student["id"]}
    ).json()
    drafts = [
        note
        for note in notes
        if note["content"] == "Summary: parent asked about homework."
    ]
    assert drafts
    assert drafts[0]["teacher_confirmed"] is False
    assert drafts[0]["source"] == "voice"

    (voice_dir() / body["object_key"]).unlink(missing_ok=True)
