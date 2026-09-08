# Outreach Candidate ID Validation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prevent the local Outreach Agent from returning recommendations for student IDs outside the current teacher's owner-scoped candidate list.

**Architecture:** Keep candidate construction unchanged. After Strands returns structured output, FastAPI compares every recommended `student_id` with the IDs supplied to the Agent and converts any mismatch into the existing browser-safe `503` response.

**Tech Stack:** FastAPI, Pydantic, pytest, Strands Agent boundary.

## Global Constraints

- Do not call Bedrock in automated tests.
- Do not change candidate fields or send additional student data.
- Do not create calls, messages, or follow-ups.
- Do not modify, merge, or push `main`.
- Do not commit or push as part of this task.

---

### Task 1: Reject recommendations outside the authorized candidates

**Files:**
- Modify: `backend/tests/test_outreach_plan.py`
- Modify: `backend/app/services/outreach_plan_client.py`

**Interfaces:**
- Consumes: `invoke_outreach_agent(candidates: list[dict[str, Any]])`.
- Produces: an `OutreachPlanResponse` only when every returned `student_id` appears in `candidates`; otherwise raises `OutreachAgentUnavailable`.

- [ ] **Step 1: Write a failing route test**

Add a test that mocks `generate_plan()` to return a valid UUID not present in the sole authorized candidate and asserts that `POST /api/v1/ai/outreach-plan/generate` returns the existing safe `503` detail.

- [ ] **Step 2: Verify the test fails for the intended reason**

Run: `../.venv/bin/python -m pytest tests/test_outreach_plan.py::test_outreach_plan_rejects_agent_student_outside_authorized_candidates -q -p no:cacheprovider`

Expected: FAIL because the current client accepts the unknown UUID and returns HTTP 200.

- [ ] **Step 3: Add the minimal allowlist check**

Build a set of stringified candidate IDs, construct the validated response, and raise `OutreachAgentUnavailable` if any response item is outside that set.

- [ ] **Step 4: Verify focused and complete suites**

Run the focused test, all backend tests, all frontend tests, `npm run build`, and `git diff --check`.

Expected: all commands pass; no real Bedrock or Twilio call occurs.
