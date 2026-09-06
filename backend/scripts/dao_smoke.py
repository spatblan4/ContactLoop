"""DAO smoke test: exercises every DAO against a temporary SQLite database.

Requires only sqlalchemy and pydantic-settings:

    python backend/scripts/dao_smoke.py
"""
import os
import shutil
import sys
import tempfile
import time
import uuid
from datetime import datetime
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

TMP_DIR = Path(tempfile.mkdtemp(prefix="contactloop_smoke_"))
os.environ.pop("SUPABASE_DB_URL", None)
os.environ.pop("DATABASE_URL", None)
os.environ["SQLITE_PATH"] = (TMP_DIR / "contactloop.db").as_posix()

from app.core.database import SessionLocal, database_mode, init_db
from app.core.exceptions import ConflictError, NotFoundError
from app.dao import (
    AiContactBriefDAO,
    ContactEventDAO,
    FollowUpDAO,
    GuardianDAO,
    StudentDAO,
    TeacherNoteDAO,
)

PASSED = []


def check(label, condition):
    if not condition:
        raise AssertionError(f"SMOKE FAILED: {label}")
    PASSED.append(label)
    print(f"ok - {label}")


def expect_raises(label, exc_type, fn, *args, **kwargs):
    try:
        fn(*args, **kwargs)
    except exc_type:
        PASSED.append(label)
        print(f"ok - {label}")
        return
    except Exception as exc:
        raise AssertionError(f"SMOKE FAILED: {label} raised {type(exc).__name__}: {exc}") from exc
    raise AssertionError(f"SMOKE FAILED: {label} raised no {exc_type.__name__}")


def main():
    init_db()
    check("sqlite fallback selected", database_mode() == "sqlite")

    db = SessionLocal()
    try:
        actor = uuid.uuid4()
        editor = uuid.uuid4()

        students = StudentDAO(db)
        guardians = GuardianDAO(db)
        events = ContactEventDAO(db)
        follow_ups = FollowUpDAO(db)
        notes = TeacherNoteDAO(db)
        briefs = AiContactBriefDAO(db)

        amara = students.create(
            {
                "name": "Amara Okafor",
                "first_name": "Amara",
                "last_name": "Okafor",
                "initials": "AO",
                "accent": "lavender",
            },
            actor_id=actor,
        )
        db.commit()
        check(
            "student created with audit timestamps",
            amara.created_at is not None and amara.updated_at is not None,
        )
        check(
            "student audit actors stamped on create",
            amara.created_by == actor and amara.updated_by == actor,
        )
        first_updated_at = amara.updated_at
        time.sleep(0.02)
        amara = students.update(amara.id, {"name": "Amara Okafor-Smith"}, actor_id=editor)
        db.commit()
        check("student name updated", amara.name == "Amara Okafor-Smith")
        check("student updated_at bumped on mutation", amara.updated_at > first_updated_at)
        check("student updated_by restamped on mutation", amara.updated_by == editor)
        check("student created_by unchanged by update", amara.created_by == actor)

        grace = guardians.create(
            {"student_id": amara.id, "name": "Grace Okafor", "relation": "Mother", "phone": "+15550100"},
            actor_id=actor,
        )
        dan = guardians.create(
            {"student_id": amara.id, "name": "Dan Okafor", "relation": "Father", "phone": "+15550101"},
            actor_id=actor,
        )
        db.commit()
        check(
            "guardians listed for student",
            [g.name for g in guardians.list(student_id=amara.id)] == ["Dan Okafor", "Grace Okafor"],
        )
        grace = guardians.update(grace.id, {"preferred_contact_method": "phone"}, actor_id=editor)
        check("guardian update persisted", grace.preferred_contact_method == "phone")
        check("student search by name", [s.id for s in students.list(search="Okafor-Smith")] == [amara.id])
        check("student search by initials", [s.id for s in students.list(search="AO")] == [amara.id])
        check("student search by guardian name", [s.id for s in students.list(search="Grace")] == [amara.id])
        check("student search by guardian phone", [s.id for s in students.list(search="+15550101")] == [amara.id])
        dan = guardians.soft_delete(dan.id, actor_id=editor)
        db.commit()
        check(
            "soft-deleted guardian hidden from list",
            [g.id for g in guardians.list(student_id=amara.id)] == [grace.id],
        )
        check("soft-deleted guardian not fetchable", guardians.get(dan.id) is None)
        check("alive guardians exposed via relationship", [g.id for g in amara.guardians] == [grace.id])
        check("search ignores soft-deleted guardians", students.list(search="+15550101") == [])
        expect_raises("guardian require raises NotFoundError", NotFoundError, guardians.require, dan.id)

        benny = students.create({"name": "Benny Lin", "initials": "BL"}, actor_id=actor)
        mei = guardians.create(
            {"student_id": benny.id, "name": "Mei Lin", "relation": "Mother", "phone": "+15550200"},
            actor_id=actor,
        )
        jae = guardians.create(
            {"student_id": benny.id, "name": "Jae Lin", "relation": "Father", "phone": "+15550201"},
            actor_id=actor,
        )
        db.commit()

        e1 = events.create(
            {
                "student_id": benny.id,
                "guardian_id": mei.id,
                "result": "No Answer",
                "call_time": datetime(2026, 1, 5, 10, 0, 0),
                "ended_at": datetime(2026, 1, 5, 10, 0, 0),
                "attempt_number": 99,
            },
            actor_id=actor,
        )
        db.commit()
        check("attempt_number computed server-side", e1.attempt_number == 1)
        check("event audit stamped on create", e1.created_by == actor)
        fu1 = follow_ups.get_open(benny.id, mei.id)
        check(
            "No Answer opens follow-up due ended_at + 1 day",
            fu1 is not None
            and fu1.due_at == datetime(2026, 1, 6, 10, 0, 0)
            and fu1.contact_event_id == e1.id
            and fu1.status == "open",
        )

        e2 = events.create(
            {"student_id": benny.id, "guardian_id": mei.id, "result": "No Answer", "ended_at": datetime(2026, 1, 6, 11, 0, 0)},
            actor_id=actor,
        )
        db.commit()
        check("second attempt numbered", e2.attempt_number == 2)
        fu1 = follow_ups.get_open(benny.id, mei.id)
        check("No Answer upserts existing open follow-up", fu1.due_at == datetime(2026, 1, 7, 11, 0, 0))
        check(
            "one open follow-up per student+guardian",
            len(follow_ups.list(status="open", student_id=benny.id)) == 1,
        )
        expect_raises(
            "duplicate open follow-up conflicts",
            ConflictError,
            follow_ups.create,
            {"student_id": benny.id, "guardian_id": mei.id, "due_at": datetime(2026, 1, 8, 9, 0, 0)},
        )
        expect_raises(
            "invalid event result rejected",
            ValueError,
            events.create,
            {"student_id": benny.id, "guardian_id": mei.id, "result": "Voicemail"},
        )

        e3 = events.create(
            {"student_id": benny.id, "guardian_id": mei.id, "result": "Busy", "ended_at": datetime(2026, 1, 7, 9, 0, 0)},
            actor_id=actor,
            follow_up_due_at=datetime(2026, 1, 9, 8, 0, 0),
        )
        db.commit()
        fu1 = follow_ups.get_open(benny.id, mei.id)
        check(
            "caller-supplied follow_up_due_at wins",
            e3.attempt_number == 3 and fu1.due_at == datetime(2026, 1, 9, 8, 0, 0),
        )

        e4 = events.create(
            {"student_id": benny.id, "guardian_id": mei.id, "result": "Failed", "ended_at": datetime(2026, 1, 8, 9, 0, 0)},
            actor_id=actor,
        )
        db.commit()
        fu1 = follow_ups.get_open(benny.id, mei.id)
        check(
            "Failed upserts open follow-up due next day",
            e4.attempt_number == 4 and fu1.due_at == datetime(2026, 1, 9, 9, 0, 0),
        )

        e5 = events.create(
            {
                "student_id": benny.id,
                "guardian_id": mei.id,
                "result": "Connected",
                "ended_at": datetime(2026, 1, 8, 10, 0, 0),
                "duration_seconds": 300,
                "discussed_topics": ["attendance", "homework"],
            },
            actor_id=actor,
        )
        db.commit()
        check("Connected increments attempts", e5.attempt_number == 5)
        check("Connected closes open follow-up", follow_ups.get_open(benny.id, mei.id) is None)
        completed = follow_ups.get(fu1.id)
        check(
            "completed follow-up stamped",
            completed.status == "completed"
            and completed.completed_at is not None
            and completed.contact_event_id == e5.id,
        )

        e6 = events.create(
            {"student_id": benny.id, "guardian_id": jae.id, "result": "No Answer", "ended_at": datetime(2026, 1, 8, 10, 0, 0)},
            actor_id=actor,
        )
        fu2 = follow_ups.get_open(benny.id, jae.id)
        check(
            "per-guardian attempt numbering",
            e6.attempt_number == 1
            and fu2 is not None
            and fu2.due_at == datetime(2026, 1, 9, 10, 0, 0),
        )

        e7 = events.create(
            {
                "student_id": benny.id,
                "guardian_id": jae.id,
                "result": "Connected",
                "ended_at": datetime(2026, 1, 8, 12, 0, 0),
                "follow_up_id": fu2.id,
            },
            actor_id=actor,
        )
        db.commit()
        check(
            "caller-supplied follow_up_id closed",
            e7.attempt_number == 2 and follow_ups.get(fu2.id).status == "completed",
        )

        e8 = events.create(
            {"student_id": benny.id, "guardian_id": mei.id, "result": "No Answer"},
            actor_id=actor,
        )
        db.commit()
        check(
            "no follow-up sync without ended_at",
            follow_ups.get_open(benny.id, mei.id) is None and e8.attempt_number == 6,
        )

        e9 = events.create(
            {"student_id": benny.id, "guardian_id": mei.id, "result": "No Answer", "ended_at": datetime(2026, 1, 9, 10, 0, 0)},
            actor_id=actor,
        )
        fu3 = follow_ups.get_open(benny.id, mei.id)
        check(
            "pre-update open follow-up exists",
            fu3 is not None and fu3.due_at == datetime(2026, 1, 10, 10, 0, 0),
        )
        e9 = events.update(e9.id, {"result": "Connected"}, actor_id=editor)
        db.commit()
        check(
            "update re-runs follow-up sync",
            follow_ups.get_open(benny.id, mei.id) is None
            and follow_ups.get(fu3.id).status == "completed"
            and follow_ups.get(fu3.id).contact_event_id == e9.id,
        )

        e10 = events.create(
            {"student_id": benny.id, "guardian_id": mei.id, "result": "No Answer", "ended_at": datetime(2026, 1, 10, 10, 0, 0)},
            actor_id=actor,
        )
        fu4 = follow_ups.get_open(benny.id, mei.id)
        events.update(e10.id, {"topic": "math camp"}, actor_id=actor)
        db.commit()
        check(
            "update without result/ended_at does not re-sync",
            follow_ups.get_open(benny.id, mei.id).id == fu4.id
            and follow_ups.get(fu4.id).due_at == datetime(2026, 1, 11, 10, 0, 0),
        )

        events.soft_delete(e10.id, actor_id=editor)
        e11 = events.create(
            {"student_id": benny.id, "guardian_id": mei.id, "result": "No Answer", "ended_at": datetime(2026, 1, 11, 10, 0, 0)},
            actor_id=actor,
        )
        db.commit()
        check("soft-deleted events excluded from attempt count", e11.attempt_number == 8)
        check("soft-deleted event hidden", events.get(e10.id) is None)
        check(
            "event list filters by result",
            [e.id for e in events.list(student_id=benny.id, result="Connected")] == [e5.id, e7.id, e9.id],
        )
        check(
            "event list filters by date range",
            [e.id for e in events.list(student_id=benny.id, date_from=datetime(2026, 1, 5, 0, 0, 0), date_to=datetime(2026, 1, 5, 23, 59, 59))] == [e1.id],
        )
        check("benny event count after soft delete", len(events.list(student_id=benny.id)) == 10)

        carla = students.create({"name": "Carla Mendes", "initials": "CM"}, actor_id=actor)
        carla_guardian = guardians.create(
            {"student_id": carla.id, "name": "Rosa Mendes", "relation": "Mother", "phone": "+15550300"},
            actor_id=actor,
        )

        note = notes.create(
            {"student_id": carla.id, "content": "Spoke about attendance.", "source": "typed"},
            actor_id=actor,
        )
        db.commit()
        check("teacher note created", note.teacher_confirmed is False and note.source == "typed")
        note = notes.update(
            note.id,
            {"content": "Spoke about attendance and homework.", "teacher_confirmed": True},
            actor_id=editor,
        )
        db.commit()
        check(
            "teacher note updated",
            note.teacher_confirmed is True
            and note.content == "Spoke about attendance and homework.",
        )
        linked = notes.create(
            {"student_id": carla.id, "contact_event_id": e1.id, "content": "Voice summary.", "source": "voice"},
            actor_id=actor,
        )
        check(
            "teacher notes listed per student",
            {n.id for n in notes.list(student_id=carla.id)} == {note.id, linked.id},
        )
        expect_raises(
            "empty teacher note rejected",
            ValueError,
            notes.create,
            {"student_id": carla.id, "content": "   "},
        )
        expect_raises(
            "invalid teacher note source rejected",
            ValueError,
            notes.create,
            {"student_id": carla.id, "content": "hello", "source": "email"},
        )
        notes.soft_delete(linked.id, actor_id=actor)
        db.commit()
        check(
            "soft-deleted teacher note hidden",
            [n.id for n in notes.list(student_id=carla.id)] == [note.id],
        )

        brief = briefs.create(
            {
                "student_id": carla.id,
                "date_from": datetime(2026, 1, 1),
                "date_to": datetime(2026, 1, 31),
                "key_topics": ["attendance"],
                "parent_concerns": ["late pickup"],
                "recorded_resolutions": ["bus schedule"],
                "open_items": ["homework plan"],
                "suggested_next_step": "Call again next week",
            },
            actor_id=actor,
        )
        db.commit()
        check(
            "ai brief created as draft",
            brief.status == "draft" and brief.version == 1 and brief.approved_at is None,
        )
        expect_raises(
            "duplicate ai brief version conflicts",
            ConflictError,
            briefs.create,
            {"student_id": carla.id, "date_from": datetime(2026, 1, 1), "date_to": datetime(2026, 1, 31)},
        )
        v2 = briefs.create(
            {"student_id": carla.id, "date_from": datetime(2026, 1, 1), "date_to": datetime(2026, 1, 31), "version": 2, "open_items": ["spring trip"]},
            actor_id=actor,
        )
        db.commit()
        check("second ai brief version accepted", v2.version == 2)
        v2 = briefs.approve(v2.id, actor_id=editor)
        db.commit()
        check(
            "ai brief approve stamps approved_at",
            v2.status == "approved" and v2.approved_at is not None and v2.updated_by == editor,
        )
        v2 = briefs.supersede(v2.id, actor_id=editor)
        db.commit()
        check("ai brief supersede sets status", v2.status == "superseded")
        check("latest ai brief skips superseded", briefs.list(student_id=carla.id, latest=True).id == brief.id)
        check("ai brief list per student", len(briefs.list(student_id=carla.id)) == 2)
        brief = briefs.update(brief.id, {"suggested_next_step": "Email summary"}, actor_id=editor)
        check("ai brief update persisted", brief.suggested_next_step == "Email summary")

        carla_event = events.create(
            {"student_id": carla.id, "result": "No Answer", "ended_at": datetime(2026, 2, 1, 9, 0, 0)},
            actor_id=actor,
        )
        db.commit()
        check("guardian-less event opens follow-up", follow_ups.get_open(carla.id, None) is not None)

        students.soft_delete(carla.id, actor_id=editor)
        db.commit()
        check("student soft-deleted", students.get(carla.id) is None)
        check("cascade hides guardians", guardians.list(student_id=carla.id) == [])
        check("cascade hides contact events", events.list(student_id=carla.id) == [])
        check("cascade hides follow-ups", follow_ups.list(student_id=carla.id) == [])
        check("cascade hides teacher notes", notes.list(student_id=carla.id) == [])
        check("cascade hides ai briefs", briefs.list(student_id=carla.id) == [])
        expect_raises("soft-deleted student require raises", NotFoundError, students.require, carla.id)
        check(
            "other students survive cascade",
            {s.id for s in students.list()} == {amara.id, benny.id},
        )
        check("other students' events survive cascade", len(events.list(student_id=benny.id)) == 10)
    finally:
        db.close()

    fresh = SessionLocal()
    try:
        students = StudentDAO(fresh)
        benny = students.get(benny.id)
        check(
            "audit values persist across sessions",
            benny is not None
            and benny.created_by == actor
            and benny.updated_at is not None
            and benny.deleted_at is None,
        )
    finally:
        fresh.close()

    print(f"\nSMOKE OK: {len(PASSED)} checks passed (sqlite at {TMP_DIR})")
    shutil.rmtree(TMP_DIR, ignore_errors=True)


if __name__ == "__main__":
    main()
