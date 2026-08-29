# Student Edit and Delete Persistence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add persistent editing for student and primary guardian details and make deletion survive page refreshes in Demo and Beta modes.

**Architecture:** Extend the existing Supabase data helpers with an `updateStudent` operation that updates the student and primary guardian rows. Add an edit modal beside the existing delete modal, then reload data after successful mutations so the UI reflects the database source of truth. Preserve the existing dependent-first deletion order and RLS behavior.

**Tech Stack:** Vanilla JavaScript, Supabase JS, Node test runner, Vite.

## Global Constraints

- Edit exactly student name, guardian name, relationship, and phone.
- Use the active Supabase client; do not treat local state as persistence.
- Keep Demo anonymous policies and Beta authenticated RLS separate.
- Do not alter unrelated contact history or AI behavior.

---

### Task 1: Add data-layer tests and helpers

**Files:**
- Modify: `/Users/chongchongchao/Documents/ChatGPT/Noteless EDU/src/lib/supabase.js`
- Test: `/Users/chongchongchao/Documents/ChatGPT/Noteless EDU/tests/student-actions.test.js`

**Interfaces:**
- `updateStudent({ studentId, guardianId, name, guardianName, relation, phone })` updates `students.name` and the selected guardian fields.
- `deleteStudent(studentId)` remains dependent-first and awaits every delete request.

- [ ] Write failing tests for the exact update payload and delete request sequence.
- [ ] Run `node --test tests/student-actions.test.js` and confirm the new tests fail for missing behavior.
- [ ] Implement the smallest helpers and preserve existing error propagation.
- [ ] Run the focused test file and confirm it passes.

### Task 2: Add edit modal and persistence flow

**Files:**
- Modify: `/Users/chongchongchao/Documents/ChatGPT/Noteless EDU/src/app.js`
- Modify: `/Users/chongchongchao/Documents/ChatGPT/Noteless EDU/src/styles.css`

**Interfaces:**
- The student menu renders `data-action="edit-student"`.
- `openEditStudent(studentId)` opens a modal prefilled from the selected student.
- `saveEditedStudent()` calls `updateStudent`, then calls `refreshData()` before closing and rendering.

- [ ] Add the Edit action to each student card menu.
- [ ] Add the edit modal with four labeled inputs and Save/Cancel controls.
- [ ] Wire menu, submit, busy, and error states.
- [ ] Keep the modal open on database failure and show the returned error.
- [ ] Add focused style rules matching the existing modal and form design.

### Task 3: Make delete refresh from the database

**Files:**
- Modify: `/Users/chongchongchao/Documents/ChatGPT/Noteless EDU/src/app.js`

- [ ] After `deleteStudent(id)` resolves, call `refreshData()` before clearing modal state and rendering the Students screen.
- [ ] Do not remove the student from local state as the only success path.
- [ ] Preserve current error behavior when a delete request fails.

### Task 4: Verify the complete behavior

**Files:**
- No additional production files.

- [ ] Run `node --test tests/*.test.js` and confirm all tests pass.
- [ ] Run `npm run build` and confirm Vite exits successfully.
- [ ] Run `git diff --check` and confirm no whitespace errors.
- [ ] Inspect the final diff and verify only the requested edit/delete behavior changed.
