"""Voice-note transcription pipeline (Phase 2).

When Amazon Transcribe is configured (``VOICE_TRANSCRIBE_ENABLED`` with AWS
credentials), uploaded voice notes are transcribed in a background thread and
an unconfirmed teacher-note draft is created. Without configuration the
original stub behavior is kept.
"""

import logging
import threading
import uuid
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session as DbSession

from app.core.config import settings
from app.models import User, VoiceNoteObject

logger = logging.getLogger(__name__)

TRANSCRIPT_STUB = "(Voice note saved locally. Transcription is not configured.)"

# In-memory job registry: {job_id: {"status": ..., "transcript": ..., "error": ...}}
# Good enough for the single-process deployment; jobs are best-effort.
_JOBS: dict[str, dict] = {}
_JOBS_LOCK = threading.Lock()

MAX_TRANSCRIPT_CHARS = 4000
MAX_POLL_SECONDS = 300
POLL_INTERVAL_SECONDS = 3


def transcribe_enabled() -> bool:
    return bool(
        settings.voice_transcribe_enabled
        and settings.aws_region
        and settings.voice_transcribe_bucket
    )


def start_transcription_job(
    db: DbSession,
    user: User,
    record: VoiceNoteObject,
    file_path: Path,
) -> str:
    """Start (or stub) transcription for an uploaded voice note."""
    job_id = uuid.uuid4().hex
    with _JOBS_LOCK:
        _JOBS[job_id] = {"status": "processing", "user_id": str(user.id)}
    if not transcribe_enabled():
        with _JOBS_LOCK:
            _JOBS[job_id] = {
                "status": "completed",
                "transcript": TRANSCRIPT_STUB,
                "user_id": str(user.id),
            }
        return job_id

    # Pass plain values: the ORM objects belong to the request session.
    thread = threading.Thread(
        target=_run_job,
        args=(job_id, user.id, record.student_id, file_path),
        daemon=True,
        name=f"voice-transcribe-{job_id[:8]}",
    )
    thread.start()
    return job_id


def get_job(job_id: str, user_id: Any = None) -> dict | None:
    with _JOBS_LOCK:
        job = _JOBS.get(job_id)
        if job is None:
            return None
        if user_id is not None and job.get("user_id") != str(user_id):
            return None
        return dict(job)


def _run_job(
    job_id: str,
    user_id: Any,
    student_id: Any,
    file_path: Path,
) -> None:
    try:
        transcript = _transcribe_file(file_path)
        _finalize_draft(job_id, user_id, student_id, transcript)
    except Exception as error:  # fail-closed: surface the failure on the job
        logger.warning("Voice transcription job %s failed.", job_id, exc_info=True)
        with _JOBS_LOCK:
            _JOBS[job_id] = {
                "status": "failed",
                "error": str(error),
                "user_id": str(user_id),
            }


def _transcribe_file(file_path: Path) -> str:
    """Call Amazon Transcribe; returns the plain transcript text."""
    import boto3
    import time

    s3 = boto3.client("s3", region_name=settings.aws_region)
    bucket = settings.voice_transcribe_bucket
    key = f"voice-notes/{file_path.name}"
    s3.upload_file(str(file_path), bucket, key)

    job_name = f"contactloop-{file_path.name}-{int(time.time())}"
    deadline = time.monotonic() + MAX_POLL_SECONDS
    transcribe = boto3.client("transcribe", region_name=settings.aws_region)
    transcribe.start_transcription_job(
        TranscriptionJobName=job_name,
        Media={"MediaFileUri": f"s3://{bucket}/{key}"},
        MediaFormat=_media_format(file_path),
        LanguageCode=settings.voice_transcribe_language,
    )

    while True:
        response = transcribe.get_transcription_job(TranscriptionJobName=job_name)
        status = response["TranscriptionJob"]["TranscriptionJobStatus"]
        if status == "COMPLETED":
            uri = response["TranscriptionJob"]["Transcript"]["TranscriptFileUri"]
            import httpx

            document = httpx.get(uri, timeout=settings.supabase_function_timeout_seconds).json()
            return str(
                document.get("results", {}).get("transcripts", [{}])[0].get(
                    "transcript", ""
                )
            )[:MAX_TRANSCRIPT_CHARS]
        if status == "FAILED":
            raise RuntimeError("Amazon Transcribe job failed.")
        if time.monotonic() > deadline:
            raise RuntimeError(
                "Amazon Transcribe job did not finish within "
                f"{MAX_POLL_SECONDS} seconds."
            )
        time.sleep(POLL_INTERVAL_SECONDS)


def _media_format(file_path: Path) -> str:
    suffix = file_path.suffix.lstrip(".").lower()
    return suffix if suffix in {"mp3", "mp4", "wav", "flac", "ogg", "amr", "webm"} else "webm"


def _finalize_draft(
    job_id: str,
    user_id: Any,
    student_id: Any,
    transcript: str,
) -> None:
    """Create an unconfirmed teacher-note draft from the transcript."""
    from app.api.deps import get_db
    from app.services.note_drafts import create_teacher_note_draft, draft_note_content

    db = next(get_db())
    try:
        try:
            content = draft_note_content({"transcript": transcript})
        except Exception:
            logger.warning("Falling back to raw transcript for note draft.")
            content = f"[Draft from voice transcript]\n{transcript}"
        create_teacher_note_draft(
            db, _user(db, user_id), student_id, content, source="voice"
        )
        with _JOBS_LOCK:
            _JOBS[job_id] = {"status": "completed", "transcript": transcript}
    finally:
        db.close()


def _user(db: DbSession, user_id: Any) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise RuntimeError("user not found")
    return user
