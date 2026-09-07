import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.dao import GuardianDAO, StudentDAO
from app.models import User
from app.schemas.import_students import ImportStudentsRequest, ImportStudentsResponse

router = APIRouter(prefix="/import", tags=["import"])


def _display_name(row) -> str:
    if row.name:
        return row.name
    return f"{row.first_name or ''} {row.last_name or ''}".strip()


def _initials(first_name: str | None, last_name: str | None, name: str) -> str:
    if first_name and last_name:
        return f"{first_name[0]}{last_name[0]}".upper()
    words = name.split()
    return "".join(word[0] for word in words[:2]).upper()


@router.post("/students", response_model=ImportStudentsResponse)
def import_students(
    payload: ImportStudentsRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    students_dao = StudentDAO(db)
    guardians_dao = GuardianDAO(db)
    owner_id = user.id

    existing = {
        (student.name, student.owner_id): student
        for student in students_dao.list(owner_id=owner_id)
    }
    key_to_student: dict[str, object] = {}
    imported_students = 0
    for row in payload.students:
        name = _display_name(row)
        match = existing.get((name, owner_id))
        updates = {
            key: value
            for key, value in {
                "name": name,
                "first_name": row.first_name,
                "last_name": row.last_name,
            }.items()
            if value is not None
        }
        if match is not None:
            student = students_dao.update(match.id, updates, actor_id=user.id)
        else:
            data = {
                **updates,
                "initials": _initials(row.first_name, row.last_name, name),
                "owner_id": owner_id,
            }
            student = students_dao.create(data, actor_id=user.id)
            existing[(student.name, student.owner_id)] = student
        key_to_student[row.student_key] = student
        imported_students += 1

    imported_guardians = 0
    for row in payload.guardians:
        student = key_to_student.get(row.student_key)
        if student is None:
            raise ValueError(
                f"guardian references unknown student_key {row.student_key!r}"
            )
        student_guardians = {
            guardian.name: guardian
            for guardian in guardians_dao.list(student_id=student.id)
        }
        match = student_guardians.get(row.name)
        if match is not None:
            updates = {
                key: value
                for key, value in {
                    "relation": row.relationship,
                    "phone": row.phone,
                    "email": row.email,
                }.items()
                if value is not None
            }
            if updates:
                guardians_dao.update(match.id, updates, actor_id=user.id)
        else:
            guardians_dao.create(
                {
                    "student_id": student.id,
                    "name": row.name,
                    "relation": row.relationship,
                    "phone": row.phone,
                    "email": row.email,
                },
                actor_id=user.id,
            )
        imported_guardians += 1

    db.commit()
    return ImportStudentsResponse(
        imported_students=imported_students,
        imported_guardians=imported_guardians,
    )
