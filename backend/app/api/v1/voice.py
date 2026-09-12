import re
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.config import settings
from app.core.exceptions import NotFoundError
from app.models import User, VoiceNoteObject
from app.services.ownership import require_owned_student
from app.services.voice_transcription import (
    TRANSCRIPT_STUB,
    get_job,
    start_transcription_job,
)

router = APIRouter(prefix="/voice", tags=["voice"])

DEFAULT_VOICE_DIR = Path(__file__).resolve().parents[3] / "data" / "voice_notes"
OBJECT_KEY_PATTERN = re.compile(r"^[A-Za-z0-9._-]{1,200}$")


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


def voice_dir() -> Path:
    return Path(settings.voice_notes_dir) if settings.voice_notes_dir else DEFAULT_VOICE_DIR


def _require_owned_voice_note(
    db: Session, object_key: str, user: User
) -> VoiceNoteObject:
    record = db.scalar(
        select(VoiceNoteObject).where(
            VoiceNoteObject.object_key == object_key,
            VoiceNoteObject.user_id == user.id,
            VoiceNoteObject.deleted_at.is_(None),
        )
    )
    if record is None:
        raise NotFoundError("voice note not found")
    return record


@router.post("/uploads", response_model=VoiceUploadResponse)
def create_voice_upload(
    payload: VoiceUploadRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_owned_student(db, payload.student_id, user.id)
    object_key = uuid.uuid4().hex
    db.add(
        VoiceNoteObject(
            object_key=object_key,
            student_id=payload.student_id,
            user_id=user.id,
            created_by=user.id,
            updated_by=user.id,
        )
    )
    db.commit()
    return VoiceUploadResponse(
        upload_url=f"/api/v1/voice/files/{object_key}", object_key=object_key
    )


@router.put("/files/{object_key}", status_code=204)
async def upload_voice_file(
    object_key: str,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not OBJECT_KEY_PATTERN.fullmatch(object_key) or ".." in object_key:
        raise HTTPException(status_code=400, detail="invalid object key")
    _require_owned_voice_note(db, object_key, user)

    max_bytes = settings.voice_max_upload_bytes
    target_dir = voice_dir()
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / object_key
    remaining = max_bytes
    try:
        with target.open("wb") as buffer:
            async for chunk in request.stream():
                remaining -= len(chunk)
                if remaining < 0:
                    raise HTTPException(
                        status_code=413,
                        detail=f"voice note exceeds the {max_bytes} byte limit",
                    )
                buffer.write(chunk)
    except HTTPException:
        target.unlink(missing_ok=True)
        raise
    return Response(status_code=204)


@router.post("/transcriptions", response_model=VoiceTranscriptionResponse)
def start_voice_transcription(
    payload: VoiceTranscriptionRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_owned_student(db, payload.student_id, user.id)
    record = _require_owned_voice_note(db, payload.object_key, user)
    if record.student_id != payload.student_id:
        raise NotFoundError("voice note not found")
    file_path = voice_dir() / payload.object_key
    if not file_path.exists():
        raise NotFoundError("voice note not found")
    job_id = start_transcription_job(db, user, record, file_path)
    return VoiceTranscriptionResponse(job_id=job_id)


@router.get("/transcriptions/{job_id}", response_model=VoiceTranscriptionStatus)
def get_voice_transcription(job_id: str, user: User = Depends(get_current_user)):
    job = get_job(job_id, user_id=user.id)
    if job is None:
        raise NotFoundError("transcription job not found")
    status = job.get("status", "processing")
    transcript = job.get("transcript")
    if status == "completed" and transcript is None:
        transcript = TRANSCRIPT_STUB
    return VoiceTranscriptionStatus(status=status, transcript=transcript or "")
