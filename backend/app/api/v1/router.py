from fastapi import APIRouter

from app.api.v1 import (
    ai_briefs,
    auth,
    contact_events,
    dashboard,
    follow_ups,
    guardians,
    imports,
    students,
    teacher_notes,
    telephony,
    voice,
)
from app.core.config import settings
from app.core.database import database_mode

api_v1_router = APIRouter()


@api_v1_router.get("/health", tags=["meta"])
def health():
    return {"status": "ok"}


@api_v1_router.get("/meta", tags=["meta"])
def meta():
    return {"database": database_mode(), "app_env": settings.app_env}


api_v1_router.include_router(auth.router)
api_v1_router.include_router(students.router)
api_v1_router.include_router(guardians.router)
api_v1_router.include_router(contact_events.router)
api_v1_router.include_router(follow_ups.router)
api_v1_router.include_router(teacher_notes.router)
api_v1_router.include_router(ai_briefs.router)
api_v1_router.include_router(ai_briefs.ai_router)
api_v1_router.include_router(dashboard.router)
api_v1_router.include_router(imports.router)
api_v1_router.include_router(voice.router)
api_v1_router.include_router(telephony.router)
