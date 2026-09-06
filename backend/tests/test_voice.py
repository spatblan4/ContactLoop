from pathlib import Path

from app.api.v1.voice import VOICE_DIR


def test_voice_stub_flow_upload_put_and_transcription(client, make_student):
    student = make_student(guardians=[])

    response = client.post(
        "/api/v1/voice/uploads",
        json={"student_id": student["id"], "content_type": "audio/webm"},
    )
    assert response.status_code == 200
    body = response.json()
    object_key = body["object_key"]
    assert object_key
    assert body["upload_url"] == f"/api/v1/voice/files/{object_key}"

    voice_bytes = b"fake-webm-audio-bytes"
    put_response = client.put(body["upload_url"], content=voice_bytes)
    assert put_response.status_code == 204
    saved = VOICE_DIR / object_key
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
