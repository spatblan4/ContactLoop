from pydantic import BaseModel, Field

from app.schemas.ai_brief import AiBriefRead
from app.schemas.contact_event import ContactEventRead
from app.schemas.follow_up import FollowUpRead
from app.schemas.student import StudentRead
from app.schemas.teacher_note import TeacherNoteRead


class ContactLoopData(BaseModel):
    students: list[StudentRead] = Field(default_factory=list)
    events: list[ContactEventRead] = Field(default_factory=list)
    follow_ups: list[FollowUpRead] = Field(default_factory=list)
    teacher_notes: list[TeacherNoteRead] = Field(default_factory=list)
    ai_briefs: list[AiBriefRead] = Field(default_factory=list)


class DashboardSummary(BaseModel):
    call_attempts: int
    connected: int
    unsuccessful: int
    follow_ups_due: int
