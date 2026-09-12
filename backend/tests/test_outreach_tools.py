"""Phase 2: owner-scoped read-only agent tools and their isolation."""

import uuid

import pytest

pytest.importorskip("strands", reason="strands-agents is not installed")

from app.api.deps import get_db  # noqa: E402
from app.core.exceptions import NotFoundError  # noqa: E402
from app.services.outreach_tools import build_outreach_tools  # noqa: E402
from tests.test_auth import make_user  # noqa: E402


def _tools_for(teacher):
    db = next(get_db())
    tools = build_outreach_tools(db, teacher["user"]["id"], [])
    return db, {name: tool for tool, name in tools}


def test_contact_history_returns_only_owned_students(client, make_user, make_student, make_event):
    from tests.test_auth import auth_headers

    teacher = make_user()
    other = make_user()
    headers = auth_headers(teacher["token"])
    mine = make_student(headers=headers)
    theirs = make_student(headers=auth_headers(other["token"]))
    make_event(mine["id"], headers=headers, result="Connected")
    make_event(theirs["id"], headers=auth_headers(other["token"]), result="Connected")

    db, tools = _tools_for(teacher)

    history = tools["get_contact_history"](str(uuid.UUID(mine["id"])))
    assert isinstance(history, list)
    assert history and history[0]["result"] == "Connected"
    assert "phone" not in str(history).lower()

    with pytest.raises(NotFoundError):
        tools["get_contact_history"](theirs["id"])


def test_open_follow_ups_and_notes_are_owner_scoped(client, make_user, make_student, make_follow_up, make_note):
    from tests.test_auth import auth_headers

    teacher = make_user()
    other = make_user()
    headers = auth_headers(teacher["token"])
    mine = make_student(headers=headers)
    theirs = make_student(headers=auth_headers(other["token"]))
    make_follow_up(mine["id"], due_at="2026-09-13T09:00:00Z", headers=headers)
    make_follow_up(theirs["id"], due_at="2026-09-13T09:00:00Z", headers=auth_headers(other["token"]))
    make_note(mine["id"], content="Confirmed context", teacher_confirmed=True, headers=headers)
    make_note(theirs["id"], content="Other teacher", teacher_confirmed=True, headers=auth_headers(other["token"]))

    db, tools = _tools_for(teacher)

    follow_ups = tools["get_open_follow_ups"]()
    assert [f["student_id"] for f in follow_ups] == [str(uuid.UUID(mine["id"]))]

    notes = tools["get_teacher_notes"](str(uuid.UUID(mine["id"])))
    assert notes == [
        {"content": "Confirmed context", "source": "typed", "teacher_confirmed": True}
    ]

    with pytest.raises(NotFoundError):
        tools["get_teacher_notes"](theirs["id"])


def test_teacher_notes_only_return_confirmed_notes(client, make_user, make_student, make_note):
    from tests.test_auth import auth_headers

    teacher = make_user()
    headers = auth_headers(teacher["token"])
    mine = make_student(headers=headers)
    make_note(mine["id"], content="Unconfirmed", teacher_confirmed=False, headers=headers)

    db, tools = _tools_for(teacher)

    notes = tools["get_teacher_notes"](str(uuid.UUID(mine["id"])))
    assert notes == []
