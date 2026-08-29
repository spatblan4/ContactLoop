# Student Edit and Delete Persistence Design

## Goal

Add editing for a student's name and primary guardian details, and ensure student deletion is persisted in the active Supabase database so deleted records do not return after a refresh.

## Scope

- Add `Edit student` to the existing student-card actions menu.
- Edit student name, primary guardian name, relationship, and phone number.
- Persist edits to `students` and the primary `guardians` row.
- Keep the existing dependent-record deletion order and make the UI refresh from Supabase after a successful delete.
- Support both anonymous Demo mode and authenticated Beta mode using the existing RLS policies.

## Data flow

The edit modal loads values from the selected student in local state. On save, a Supabase helper updates the student row and its primary guardian row. The app then reloads ContactLoop data and renders the refreshed result. Delete continues to call the database helper first; only after it completes does the app reload data and navigate back to Students.

If a database operation fails, the modal stays open with an error and local state is not treated as persisted. Missing optional tables remain tolerated as in the existing delete helper.

## Verification

- Unit tests cover the edit payload and delete request sequence.
- Browser-level smoke verification checks that the edit action is visible and that save/delete handlers are wired.
- Full Node test suite, Vite production build, and `git diff --check` must pass.
