import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models import ContactEvent, User
from app.services.ownership import require_owned_resource, require_owned_student
from app.services.supabase_functions import (
    SupabaseFunctionError,
    invoke_call_status_sync,
    invoke_start_call,
)

router = APIRouter(prefix="/telephony", tags=["telephony"])


class StartCallRequest(BaseModel):
    student_id: uuid.UUID
    planned_topic: str | None = None


class CallStatusSyncRequest(BaseModel):
    event_id: uuid.UUID


class StartCallResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    eventId: str
    providerCallId: str | None = None


class CallStatusSyncResult(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    status: str | None = None


class CallStatusSyncResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    synced: list[CallStatusSyncResult] = Field(default_factory=list)


def _calling_service_error(error: SupabaseFunctionError) -> HTTPException:
    return HTTPException(status_code=502, detail=str(error))


@router.post("/calls", response_model=StartCallResponse)
def start_call(
    payload: StartCallRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_owned_student(db, payload.student_id, user.id)
    try:
        return invoke_start_call(payload.student_id, payload.planned_topic)
    except SupabaseFunctionError as error:
        raise _calling_service_error(error) from error


@router.post("/call-status-sync", response_model=CallStatusSyncResponse)
def sync_call_status(
    payload: CallStatusSyncRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_owned_resource(db, ContactEvent, payload.event_id, user.id, "Contact event")
    try:
        return invoke_call_status_sync(payload.event_id)
    except SupabaseFunctionError as error:
        raise _calling_service_error(error) from error
