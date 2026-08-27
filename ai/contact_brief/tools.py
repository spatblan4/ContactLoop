from __future__ import annotations

from strands import tool

from .supabase_reader import SupabaseContactReader


def build_contact_tools(reader: SupabaseContactReader, include_notes: bool = True):
    @tool
    def get_contact_stats(student_id: str, date_from: str, date_to: str) -> dict:
        """Get authoritative contact counts for one student and date range.

        Never calculate or infer counts from other tool results. These values come
        from a Supabase SQL RPC.
        """
        return reader.get_stats(student_id, date_from, date_to)

    @tool
    def get_teacher_notes_and_topics(student_id: str, date_from: str, date_to: str) -> list[dict]:
        """Read teacher-approved notes and selected topics for the date range."""
        return reader.get_notes_and_topics(student_id, date_from, date_to, include_notes=include_notes)

    @tool
    def get_open_follow_ups(student_id: str) -> list[dict]:
        """Read currently open follow-up records for one student."""
        return reader.get_open_follow_ups(student_id)

    return [get_contact_stats, get_teacher_notes_and_topics, get_open_follow_ups]
