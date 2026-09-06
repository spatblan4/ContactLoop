import re
import uuid
from pathlib import Path

from fastapi import APIRouter, Request, Response
from pydantic import BaseModel

router = APIRouter(prefix="/voice", tags=["voice"])

VOICE_DIR = Path(__file__).resolve().parents[3] / "data" / "voice_notes"
OBJECT_KEY_PATTERN = re.compile(r"^[A-Za-z0-9._-]{1,200}$")

TRANSCRIPT_STUB = "(Voice note saved locally. Transcription is not configured.)"


class VoiceUploadRequest(BaseModel):
    student_id: uuid.UUID
    content_type: str


class VoiceUploadResponse(BaseModel):
    upload_url: str
    object_key: str


class VoiceTranscriptionRequest(BaseModel):
    student_id: uuid.UUID
    object_key: str


class VoiceTranscriptionResponse(BaseModel):
    job_id: str


class VoiceTranscriptionStatus(BaseModel):
    status: str
    transcript: str


@router.post("/uploads", response_model=VoiceUploadResponse)
def create_voice_upload(payload: VoiceUploadRequest):
    object_key = uuid.uuid4().hex
    return VoiceUploadResponse(
        upload_url=f"/api/v1/voice/files/{object_key}", object_key=object_key
    )


@router.put("/files/{object_key}", status_code=204)
async def upload_voice_file(object_key: str, request: Request):
    if not OBJECT_KEY_PATTERN.fullmatch(object_key) or ".." in object_key:
        raise ValueError("invalid object key")
    content = await request.body()
    VOICE_DIR.mkdir(parents=True, exist_ok=True)
    (VOICE_DIR / object_key).write_bytes(content)
    return Response(status_code=204)


@router.post("/transcriptions", response_model=VoiceTranscriptionResponse)
def start_voice_transcription(payload: VoiceTranscriptionRequest):
    return VoiceTranscriptionResponse(job_id=uuid.uuid4().hex)


@router.get("/transcriptions/{job_id}", response_model=VoiceTranscriptionStatus)
def get_voice_transcription(job_id: str):
    return VoiceTranscriptionStatus(status="completed", transcript=TRANSCRIPT_STUB)
