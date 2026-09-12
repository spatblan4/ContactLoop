import uuid
from typing import Any, ClassVar, Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models import Student


class StudentScopedModel(Protocol):
    """Static contract for models scoped to a student (and therefore an owner)."""

    id: ClassVar[Any]
    student_id: ClassVar[Any]
    deleted_at: ClassVar[Any]


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


def require_owned_resource(
    db: Session,
    resource_model: type[StudentScopedModel],
    resource_id: uuid.UUID,
    owner_id: uuid.UUID,
    label: str,
) -> Any:
    resource = db.scalar(
        select(resource_model).where(
            resource_model.id == resource_id,
            resource_model.deleted_at.is_(None),
            resource_model.student_id.in_(
                select(Student.id).where(
                    Student.owner_id == owner_id,
                    Student.deleted_at.is_(None),
                )
            ),
        )
    )
    if resource is None:
        raise NotFoundError(f"{label} not found")
    return resource
