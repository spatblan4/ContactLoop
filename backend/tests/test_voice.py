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
    saved.unlink(missing_ok=True)

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
