# AI Summary Edit and Voice Notes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add versioned, teacher-controlled AI Contact Summary editing and a secure teacher voice-note pipeline using private S3, Amazon Transcribe, Supabase, and the existing Strands/Bedrock provider without changing Twilio call logic.

**Architecture:** Phase 1 adds a versioned `ai_contact_briefs` persistence layer and inline review controls. Phase 2 adds teacher-only MediaRecorder capture with server-issued presigned S3 uploads and asynchronous Transcribe jobs. Phase 3 saves only teacher-confirmed note content and explicitly creates a new draft brief version through the existing AWS provider.

**Tech Stack:** Vanilla JavaScript + Vite frontend, Supabase PostgreSQL/RLS and Edge Functions, AWS S3, Amazon Transcribe batch jobs, existing Strands Agents + Amazon Bedrock Lambda, Node built-in tests.

## Global Constraints

- Do not modify the existing Twilio call flow or provider abstraction.
- Do not record or transcribe real parent calls.
- Keep AWS credentials and Supabase service-role keys server-side.
- Keep private S3 audio temporary; delete after successful transcription and expire after one day as a lifecycle fallback.
- Store one confirmed note body in `teacher_notes.content`; do not permanently duplicate raw and confirmed transcript columns.
- AI briefs use `draft`, `approved`, and `superseded` statuses.
- Numeric statistics remain Supabase/SQL-derived and are never model-generated.
- New AI versions remain `draft` until teacher approval.

---

### Task 1: Add database versioning and teacher-notes schema

**Files:**
- Create: `supabase/patch-ai-summary-voice-notes.sql`
- Modify: `src/lib/supabase.js`
- Test: `tests/ai-summary-persistence.test.js`

**Interfaces:**
- Produces `saveAiContactBrief`, `approveAiContactBrief`, `removeAiContactBrief`, and `createTeacherNote` data operations.
- `ai_contact_briefs` stores one immutable version row per generated brief and `teacher_notes` stores only confirmed content.

- [ ] **Step 1: Write the failing test**

Add tests for a brief payload containing `student_id`, `date_from`, `date_to`, `version`, `status`, five narrative fields, and approval timestamps; assert the persistence adapter maps them without changing stats. Add a note test asserting voice content maps to `{ content, source: 'voice', teacher_confirmed: true }` and never includes `voice_transcript`.

- [ ] **Step 2: Run test to verify it fails**

Run: `node --test tests/ai-summary-persistence.test.js`
Expected: FAIL because the persistence helpers and schema contract do not exist.

- [ ] **Step 3: Write minimal implementation**

Create SQL with `ai_contact_briefs` version/status columns, a unique `(student_id, date_from, date_to, version)` constraint, `teacher_notes.content/source/teacher_confirmed`, RLS policies matching the existing teacher workspace policies, and indexes for student/date lookups. Add client helpers that insert a new brief version, approve only the selected row, mark the prior approved row superseded when a new version is created, delete a selected brief, and insert a confirmed note.

- [ ] **Step 4: Run test to verify it passes**

Run: `node --test tests/ai-summary-persistence.test.js`
Expected: PASS.

- [ ] **Step 5: Apply and verify SQL**

Run the new SQL in Supabase SQL Editor and verify the two tables, indexes, constraints, and policies exist. Do not commit credentials or service-role keys.

### Task 2: Implement Phase 1 summary editing state and actions

**Files:**
- Modify: `src/app.js`
- Modify: `src/lib/supabase.js`
- Modify: `src/styles.css`
- Test: `tests/ai-summary-editor.test.js`

**Interfaces:**
- Produces `renderAiContactSummary(id)` with view/edit states and action hooks for edit, cancel, save, approve, regenerate, and remove.
- Uses `state.aiContactBriefs[id] = { id, version, status, brief, editing, ... }`.

- [ ] **Step 1: Write the failing test**

Test pure editor helpers for adding, updating, and deleting list items in `key_topics`, `parent_concerns`, `recorded_resolutions`, and `open_items`; test that cancel returns the original snapshot and save produces a new persisted brief payload with status `draft`.

- [ ] **Step 2: Run test to verify it fails**

Run: `node --test tests/ai-summary-editor.test.js`
Expected: FAIL because editor helpers and version-aware actions are absent.

- [ ] **Step 3: Write minimal implementation**

Extract small pure helpers into `src/lib/ai-summary-editor.js`. Add inline inputs and per-item Edit/Delete controls, `+ Add` controls, and editable Suggested Next Step. Add the `•••` menu with Regenerate and Remove. Save through Supabase, show `Needs Teacher Review` for drafts, show `Teacher Approved` for approved rows, and preserve approved rows as `superseded` when regeneration creates a new version.

- [ ] **Step 4: Run focused and existing tests**

Run: `node --test tests/ai-summary-editor.test.js tests/ai-provider.test.js tests/contact-summary.test.js`
Expected: PASS.

- [ ] **Step 5: Verify build**

Run: `npm run build`
Expected: successful Vite build with no errors.

### Task 3: Connect versioned briefs to the existing AWS response

**Files:**
- Modify: `src/app.js`
- Modify: `src/lib/ai-provider.js`
- Modify: `src/lib/supabase.js`
- Test: `tests/ai-summary-versioning.test.js`

**Interfaces:**
- A generated brief is inserted as `version = max(version) + 1`, `status = draft`.
- Existing authoritative stats remain outside the editable brief payload.

- [ ] **Step 1: Write the failing test**

Test that a regenerated brief after an approved version creates version 2 as `draft`, changes version 1 to `superseded`, and leaves version 1 narrative untouched. Test that approval updates only version 2.

- [ ] **Step 2: Run test to verify it fails**

Run: `node --test tests/ai-summary-versioning.test.js`
Expected: FAIL because generation currently stores only an in-memory result and has no version transition.

- [ ] **Step 3: Write minimal implementation**

Wrap the existing provider result with a Supabase version insert and prior-version transition. Load the latest non-superseded row on page load. Keep `Regenerate summary` explicit and never auto-approve its result.

- [ ] **Step 4: Run tests and build**

Run: `node --test tests/ai-summary-versioning.test.js tests/ai-provider.test.js && npm run build`
Expected: all tests pass and build succeeds.

### Task 4: Add voice-note database and secure upload functions

**Files:**
- Create: `supabase/patch-teacher-notes.sql`
- Create: `supabase/functions/create-voice-upload/index.ts`
- Create: `supabase/functions/transcribe-voice-note/index.ts`
- Create: `supabase/functions/get-transcript-status/index.ts`
- Test: `tests/voice-functions.test.js`

**Interfaces:**
- `POST /functions/v1/create-voice-upload` returns `{ objectKey, uploadUrl }` for the authenticated student only.
- `POST /functions/v1/transcribe-voice-note` accepts `{ objectKey }` and returns `{ jobId }`.
- `POST /functions/v1/get-transcript-status` returns `{ status: 'transcribing' | 'completed' | 'failed', transcript?: string }`.

- [ ] **Step 1: Write the failing test**

Test request validation for missing/invalid student or object key, test that the transcription function never returns AWS credentials, and test status mapping for `IN_PROGRESS`, `COMPLETED`, and `FAILED`.

- [ ] **Step 2: Run test to verify it fails**

Run: `node --test tests/voice-functions.test.js`
Expected: FAIL because the Edge Functions and validation module do not exist.

- [ ] **Step 3: Write minimal implementation**

Use server-side environment variables for AWS credentials, private S3 presigned PUT URLs with a short expiration, Amazon Transcribe batch jobs, and controlled transcript output. Validate authenticated ownership before issuing URLs or job status. Delete the source object after successful transcript retrieval. Add SQL RLS for `teacher_notes`.

- [ ] **Step 4: Run tests and type checks**

Run: `node --test tests/voice-functions.test.js` and `deno check supabase/functions/create-voice-upload/index.ts supabase/functions/transcribe-voice-note/index.ts supabase/functions/get-transcript-status/index.ts`.
Expected: PASS.

- [ ] **Step 5: Deploy and configure AWS resources**

Create a private S3 bucket with a one-day lifecycle expiration, configure the Edge Function secrets, and deploy the three functions. Verify CORS allows only the local and deployed ContactLoop origins and allows the required POST/content-type headers.

### Task 5: Add Add by Voice and transcript review UI

**Files:**
- Create: `src/lib/voice-note.js`
- Modify: `src/app.js`
- Modify: `src/styles.css`
- Test: `tests/voice-note.test.js`

**Interfaces:**
- `createVoiceNoteController({ mediaDevices, recorderFactory, upload, transcribe, status })` exposes `start`, `stop`, `cancel`, and state transitions.
- UI states are `idle`, `recording`, `uploading`, `transcribing`, `review`, `saving`, `saved`, and `error`.

- [ ] **Step 1: Write the failing test**

Test the state machine transitions, that `stop` produces a Blob for upload, that failed transcription reaches a retryable error state, and that Save note is disabled until the teacher-confirmed review action.

- [ ] **Step 2: Run test to verify it fails**

Run: `node --test tests/voice-note.test.js`
Expected: FAIL because the controller and modal do not exist.

- [ ] **Step 3: Write minimal implementation**

Add `🎤 Add by voice` to the summary actions. Build the modal with Start recording, timer, Stop, Cancel, Uploading, Transcribing, Voice Transcript textarea, Try again, and Save note. Request microphone access only after Start recording. Save the edited transcript as `teacher_notes.content` with `source = 'voice'` and `teacher_confirmed = true`.

- [ ] **Step 4: Run tests and build**

Run: `node --test tests/voice-note.test.js tests/ai-summary-editor.test.js && npm run build`
Expected: PASS and successful build.

### Task 6: Explicit summary refresh after saving a voice note

**Files:**
- Modify: `src/app.js`
- Modify: `src/lib/ai-summary-editor.js`
- Modify: `src/lib/ai-provider.js`
- Test: `tests/voice-summary-refresh.test.js`

**Interfaces:**
- After saving a note, the UI shows `New context saved.` and offers `Update Summary` or `Not now`.
- Update creates the next draft version using the existing Strands/Bedrock endpoint.

- [ ] **Step 1: Write the failing test**

Test that saving a voice note does not call the AI provider, that choosing Update Summary calls it once with the latest date range and student, and that the returned brief is stored as a new `draft` version.

- [ ] **Step 2: Run test to verify it fails**

Run: `node --test tests/voice-summary-refresh.test.js`
Expected: FAIL because voice save currently has no summary refresh decision.

- [ ] **Step 3: Write minimal implementation**

Add the post-save confirmation prompt and explicit Update Summary action. Reuse existing provider error handling, preserve the previous approved version, mark newly evidenced sections with a temporary `NEW` presentation marker based on old/new item differences, and require approval again.

- [ ] **Step 4: Run full verification**

Run: `node --test tests/*.test.js && npm run build && git diff --check && python3 -m compileall -q ai`
Expected: all JavaScript tests pass, build succeeds, no whitespace errors, and Python files compile.

### Task 7: End-to-end privacy and regression verification

**Files:**
- Modify: `ai/README.md`
- Create: `docs/superpowers/runbooks/voice-notes-setup.md`
- Test: `tests/voice-privacy.test.js`

- [ ] **Step 1: Write the failing test**

Assert the browser-facing configuration contains no AWS secret names or values, the voice request payload contains no parent call/provider identifiers, and raw audio deletion is requested after successful transcript retrieval.

- [ ] **Step 2: Run test to verify it fails**

Run: `node --test tests/voice-privacy.test.js`
Expected: FAIL until the final flow and documentation expose the required privacy boundaries.

- [ ] **Step 3: Write minimal implementation**

Document environment variables, S3 lifecycle setup, Edge Function deployment, and the distinction between teacher voice notes and Twilio calls. Keep AWS credentials server-side and remove any raw audio references from returned browser payloads.

- [ ] **Step 4: Run final verification**

Run: `node --test tests/*.test.js && npm run build && git diff --check`
Expected: PASS with no build or test regressions.

