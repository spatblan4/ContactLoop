import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models import Student


def require_owned_student(
    db: Session, student_id: uuid.UUID, owner_id: uuid.UUID
) -> Student:
    student = db.scalar(
        select(Student).where(
            Student.id == student_id,
            Student.owner_id == owner_id,
            Student.deleted_at.is_(None),
        )
    )
    if student is None:
        raise NotFoundError("student not found")
    return student
