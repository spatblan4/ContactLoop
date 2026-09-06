from pydantic import BaseModel


class ImportStudentRow(BaseModel):
    student_key: str
    name: str | None = None
    first_name: str | None = None
    last_name: str | None = None


class ImportGuardianRow(BaseModel):
    student_key: str
    name: str
    relationship: str
    phone: str | None = None
    email: str | None = None


class ImportStudentsRequest(BaseModel):
    students: list[ImportStudentRow] = []
    guardians: list[ImportGuardianRow] = []


class ImportStudentsResponse(BaseModel):
    imported_students: int
    imported_guardians: int
