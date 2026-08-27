# ContactLoop Import Students Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a secure CSV/XLSX student and guardian import flow with Auth-owned Supabase data, column mapping, preview, duplicate handling, and demo/trial runtime modes.

**Architecture:** Keep the existing single-file app shell but extract import parsing and validation into pure modules. Parse files in the browser, send only teacher-confirmed structured rows to a transactional Supabase RPC, and derive ownership from `auth.uid()`. Use `VITE_APP_MODE=demo|authenticated` to keep the Hackathon demo login-free while allowing friends to use the same code with Auth and isolated trial data.

**Tech Stack:** Vite, vanilla JavaScript templates, Supabase JS Auth/PostgREST, PostgreSQL SQL migration/RPC/RLS, SheetJS `xlsx`, Node test runner.

## Global Constraints

- Demo mode skips login and uses fixed demo data; authenticated mode requires Email + Password Supabase Auth.
- Original CSV/XLSX files remain browser-only and are never stored in Supabase Storage, logs, or public console.
- Only column headers may be sent to a future AI mapper; the MVP uses local deterministic aliases and sends no roster rows to AI.
- `teacher_id` is always derived from `auth.uid()` in database functions and RLS; the browser never supplies it as an authority.
- A student supports multiple guardians through `guardians.student_id`; no fixed mom/dad columns are introduced.
- Existing dashboard, follow-up, contact-log, and call behavior remains intact outside owner-aware data queries.
- No PDF, OCR, SIS, Google Classroom, PowerSchool, or district sync work is included.

---

### Task 1: Add pure import parsing and validation modules

**Files:**
- Create: `/Users/chongchongchao/Documents/ChatGPT/Noteless EDU/src/lib/import-students.js`
- Create: `/Users/chongchongchao/Documents/ChatGPT/Noteless EDU/tests/import-students.test.js`
- Modify: `/Users/chongchongchao/Documents/ChatGPT/Noteless EDU/package.json`
- Modify: `/Users/chongchongchao/Documents/ChatGPT/Noteless EDU/package-lock.json`

**Interfaces:**
- Produces `parseCsvText(text) -> { headers: string[], rows: object[] }`.
- Produces `parseWorkbook(buffer) -> { headers: string[], rows: object[] }` using `xlsx`.
- Produces `suggestColumnMapping(headers) -> Record<string, string|null>`.
- Produces `normalizeImportRows(rows, mapping) -> NormalizedImportRow[]`.
- Produces `groupImportRows(rows) -> GroupedImportStudent[]`.
- Produces `validateImportRows(rows, existingStudents) -> { rows, stats }`.
- Produces `buildImportPayload(rows) -> { students: Array, guardians: Array }`.

- [ ] **Step 1: Write failing tests for CSV parsing and mapping**

  Add tests proving quoted CSV values, blank rows, `Child → Student Full Name`, `Parent 1 → Guardian Name`, `Cell Phone → Phone`, and unknown columns are handled without guessing.

- [ ] **Step 2: Run the focused tests and verify they fail for missing exports**

  Run: `node --test tests/import-students.test.js`
  Expected: FAIL because `src/lib/import-students.js` does not yet export the parser functions.

- [ ] **Step 3: Add the XLSX dependency and implement browser-safe parsing**

  Add `xlsx` to dependencies. Implement CSV parsing without `eval`, use `XLSX.read(buffer, { type: 'array' })` for workbooks, trim headers/cells, ignore completely blank rows, and preserve cell values as strings.

- [ ] **Step 4: Implement deterministic mapping, normalization, grouping, and validation**

  Map only known aliases. Normalize names and phone comparison keys for duplicate detection. Require student name, guardian name, and relationship for `Ready`; keep missing phone/email as empty values. Group rows by normalized student name so multiple guardians create one student group.

- [ ] **Step 5: Run focused tests and verify they pass**

  Run: `node --test tests/import-students.test.js`
  Expected: all import parser, mapping, grouping, validation, duplicate, and payload tests pass.

- [ ] **Step 6: Commit the parser slice**

  Run: `git add package.json package-lock.json src/lib/import-students.js tests/import-students.test.js && git commit -m "feat: add student import parsing"`

### Task 2: Add runtime mode and Email + Password Auth

**Files:**
- Create: `/Users/chongchongchao/Documents/ChatGPT/Noteless EDU/src/lib/app-config.js`
- Create: `/Users/chongchongchao/Documents/ChatGPT/Noteless EDU/src/lib/auth.js`
- Modify: `/Users/chongchongchao/Documents/ChatGPT/Noteless EDU/src/lib/supabase.js`
- Modify: `/Users/chongchongchao/Documents/ChatGPT/Noteless EDU/src/app.js`
- Modify: `/Users/chongchongchao/Documents/ChatGPT/Noteless EDU/src/styles.css`
- Modify: `/Users/chongchongchao/Documents/ChatGPT/Noteless EDU/.env.example`

**Interfaces:**
- `APP_MODE` is `'demo'` or `'authenticated'`, defaulting to `'demo'` for the Hackathon-safe local experience.
- `getAuthSession() -> Promise<Session|null>`.
- `signInWithPassword(email, password) -> Promise<{ data, error }>`.
- `signUpWithPassword(email, password) -> Promise<{ data, error }>`.
- `signOut() -> Promise<void>`.

- [ ] **Step 1: Write auth state tests for mode selection and unauthenticated gating**

  Test that demo mode does not require a session, authenticated mode does require one, and auth error messages are surfaced without exposing tokens.

- [ ] **Step 2: Run auth tests and verify the new behavior fails**

  Run: `node --test tests/auth.test.js`
  Expected: FAIL because mode and auth helpers do not exist.

- [ ] **Step 3: Implement app config and Supabase Auth helpers**

  Read `VITE_APP_MODE`, use `supabase.auth.getSession`, `signInWithPassword`, `signUp`, `signOut`, and `onAuthStateChange`. Do not log session tokens or user roster data.

- [ ] **Step 4: Add the login/create-account screen and authenticated app gate**

  In authenticated mode render a login screen before data loading. Provide email, password, submit mode toggle, and readable error/success states. Keep demo mode behavior unchanged.

- [ ] **Step 5: Run auth tests and the build**

  Run: `node --test tests/auth.test.js && npm run build`
  Expected: focused auth tests pass and Vite exits with code 0.

- [ ] **Step 6: Commit the auth slice**

  Run: `git add .env.example src/lib/app-config.js src/lib/auth.js src/lib/supabase.js src/app.js src/styles.css tests/auth.test.js && git commit -m "feat: add demo and authenticated runtime modes"`

### Task 3: Migrate Supabase schema, ownership, RLS, and transactional import RPC

**Files:**
- Create: `/Users/chongchongchao/Documents/ChatGPT/Noteless EDU/supabase/patch-import-students-auth.sql`
- Modify: `/Users/chongchongchao/Documents/ChatGPT/Noteless EDU/supabase/schema.sql`
- Create: `/Users/chongchongchao/Documents/ChatGPT/Noteless EDU/tests/import-sql.test.js`

**Interfaces:**
- SQL function `public.import_students(p_students jsonb, p_guardians jsonb) returns jsonb`.
- The function reads `auth.uid()`, creates students and guardians in one transaction, and returns `{ students_imported, guardians_imported }`.
- RLS policies use `auth.uid()` directly for students and an `exists` subquery through `guardians.student_id` for related tables.

- [ ] **Step 1: Write SQL contract tests**

  Add text-level tests asserting the migration adds owner/name/email columns, drops anon policies, creates authenticated owner policies, references `auth.uid()`, and defines `import_students` without accepting a teacher id argument.

- [ ] **Step 2: Run SQL contract tests and verify the missing migration fails**

  Run: `node --test tests/import-sql.test.js`
  Expected: FAIL because `supabase/patch-import-students-auth.sql` does not exist.

- [ ] **Step 3: Implement the additive migration**

  Add nullable owner/name columns for compatibility with existing seed rows, add guardian email/contact fields, and keep existing `name` / `relation` reads working. Existing unowned demo rows remain inaccessible to authenticated users.

- [ ] **Step 4: Replace anonymous policies with authenticated owner-aware policies**

  Apply policies to students, guardians, follow_ups, contact_events, ai_contact_briefs, and teacher_notes. Use student ownership checks for related rows. Do not grant authenticated users access to rows with null owner.

- [ ] **Step 5: Implement the transactional import RPC**

  Validate `auth.uid()` is non-null, insert each distinct student with `teacher_id = auth.uid()`, then insert guardians linked to the created student. Return counts. Let PostgreSQL transaction semantics roll back all inserts on error.

- [ ] **Step 6: Run SQL contract tests and review the migration manually**

  Run: `node --test tests/import-sql.test.js`
  Expected: all policy, owner, column, and RPC contract assertions pass.

- [ ] **Step 7: Commit the schema slice**

  Run: `git add supabase/schema.sql supabase/patch-import-students-auth.sql tests/import-sql.test.js && git commit -m "feat: secure student ownership and import rpc"`

### Task 4: Add owner-aware Supabase client operations

**Files:**
- Modify: `/Users/chongchongchao/Documents/ChatGPT/Noteless EDU/src/lib/supabase.js`
- Modify: `/Users/chongchongchao/Documents/ChatGPT/Noteless EDU/src/app.js`
- Create: `/Users/chongchongchao/Documents/ChatGPT/Noteless EDU/tests/supabase-import.test.js`

**Interfaces:**
- `loadContactLoopData()` returns only rows allowed by the authenticated RLS session.
- `importStudents(payload) -> Promise<{ students_imported: number, guardians_imported: number }>` calls the `import_students` RPC and never sends `teacher_id`.
- `createStudent()` uses the same owner-aware insert path and supports optional guardian email.

- [ ] **Step 1: Write failing client contract tests**

  Test that the RPC body contains only confirmed students and guardians, omits teacher_id, and converts Supabase errors into readable messages.

- [ ] **Step 2: Run the focused tests and verify failure**

  Run: `node --test tests/supabase-import.test.js`
  Expected: FAIL because `importStudents` is not exported.

- [ ] **Step 3: Implement the import RPC client and query fields**

  Add `importStudents`, include first/last/email fields in queries, preserve existing normalized app fields, and make authenticated data loading wait for a valid session.

- [ ] **Step 4: Run focused tests and existing tests**

  Run: `node --test tests/supabase-import.test.js tests/*.test.js`
  Expected: all client and existing tests pass.

- [ ] **Step 5: Commit the data access slice**

  Run: `git add src/lib/supabase.js src/app.js tests/supabase-import.test.js && git commit -m "feat: add owner-aware student import client"`

### Task 5: Implement Students empty state, onboarding CTA, and four-step import UI

**Files:**
- Create: `/Users/chongchongchao/Documents/ChatGPT/Noteless EDU/src/lib/import-students-view.js`
- Modify: `/Users/chongchongchao/Documents/ChatGPT/Noteless EDU/src/app.js`
- Modify: `/Users/chongchongchao/Documents/ChatGPT/Noteless EDU/src/styles.css`

**Interfaces:**
- `renderImportUpload(state)`, `renderImportMapping(state)`, `renderImportReview(state)`, and `renderImportComplete(result)` produce escaped HTML for each step.
- `handleImportFile(file) -> Promise<void>` parses CSV/XLSX in memory and stores headers/rows in import state.
- `confirmImportMapping(mapping) -> void` normalizes and validates rows.
- `commitReadyImport() -> Promise<void>` calls `importStudents` with ready rows and transitions to Complete.

- [ ] **Step 1: Add UI state and navigation tests**

  Test the Students header buttons, empty state buttons, Dashboard CTA only when `students.length === 0`, and no Import Students item in `navItems`.

- [ ] **Step 2: Run UI contract tests and verify missing UI fails**

  Run: `node --test tests/import-students-view.test.js`
  Expected: FAIL because import rendering functions and actions are not implemented.

- [ ] **Step 3: Add Import Students screen and Upload step**

  Add a `screen === 'import-students'` branch, file input with `.csv,.xlsx`, dropzone, Browse files, template download, back link, and clear parse errors. Keep raw file out of state after parsing.

- [ ] **Step 4: Add Match Columns step**

  Render source columns with target dropdowns, local mapping suggestions, Needs review indicators, and Continue disabled until required fields are confirmed.

- [ ] **Step 5: Add Review step and editable rows**

  Render counts, status chips, duplicate choices Skip / Import as new, inline editing for review rows, and a disabled import button when no ready rows remain.

- [ ] **Step 6: Add Complete step and refresh behavior**

  Call the RPC only after teacher confirmation, show imported counts, release parsed file state, refresh data, hide the zero-student Dashboard CTA, and provide View Students.

- [ ] **Step 7: Run UI contract tests and build**

  Run: `node --test tests/import-students-view.test.js && npm run build`
  Expected: all UI contract tests pass and the build exits with code 0.

- [ ] **Step 8: Commit the import UI slice**

  Run: `git add src/lib/import-students-view.js src/app.js src/styles.css tests/import-students-view.test.js && git commit -m "feat: add Import Students workflow"`

### Task 6: Add template download, responsive styling, and privacy-focused polish

**Files:**
- Modify: `/Users/chongchongchao/Documents/ChatGPT/Noteless EDU/src/lib/import-students.js`
- Modify: `/Users/chongchongchao/Documents/ChatGPT/Noteless EDU/src/app.js`
- Modify: `/Users/chongchongchao/Documents/ChatGPT/Noteless EDU/src/styles.css`
- Modify: `/Users/chongchongchao/Documents/ChatGPT/Noteless EDU/tests/import-students.test.js`

**Interfaces:**
- `CONTACTLOOP_TEMPLATE_HEADERS` is the exact six-column template list.
- `downloadContactLoopTemplate() -> void` downloads a generated CSV template without uploading anything.

- [ ] **Step 1: Write failing template and responsive behavior tests**

  Test exact template headers and that the import screen includes the privacy note and responsive class hooks.

- [ ] **Step 2: Implement template generation and styling**

  Generate a Blob from the six headers, add clear stepper / dropzone / mapping / review styles, preserve existing ContactLoop visual language, and add mobile rules for the table and action buttons.

- [ ] **Step 3: Run focused tests and build**

  Run: `node --test tests/import-students.test.js && npm run build`
  Expected: all focused tests pass and Vite exits with code 0.

- [ ] **Step 4: Commit the polish slice**

  Run: `git add src/lib/import-students.js src/app.js src/styles.css tests/import-students.test.js && git commit -m "feat: polish student import onboarding"`

### Task 7: End-to-end verification and environment handoff

**Files:**
- Modify: `/Users/chongchongchao/Documents/ChatGPT/Noteless EDU/.env.example`
- Create: `/Users/chongchongchao/Documents/ChatGPT/Noteless EDU/docs/runbooks/import-students-setup.md`

**Interfaces:**
- Documents exact demo and authenticated environment variables, Supabase migration order, Auth setup, and trial verification steps.

- [ ] **Step 1: Run the full JavaScript test suite**

  Run: `node --test tests/*.test.js`
  Expected: zero failures.

- [ ] **Step 2: Run the production build**

  Run: `npm run build`
  Expected: Vite exits with code 0.

- [ ] **Step 3: Verify Demo mode in a browser**

  Start with `VITE_APP_MODE=demo`, open the app, confirm no login screen, confirm existing seed students render, and confirm Dashboard does not show zero-student onboarding.

- [ ] **Step 4: Verify authenticated trial mode in a browser**

  Use a separate trial Supabase project with the migration applied. Create a teacher account, sign in, import a two-row/two-guardian fixture, refresh, confirm one student and two guardians persist, and confirm another teacher cannot read those rows.

- [ ] **Step 5: Verify privacy and repository hygiene**

  Confirm `.env.local`, roster fixtures, Supabase `.temp`, `node_modules`, `dist`, and generated files are ignored; confirm no roster values are logged.

- [ ] **Step 6: Commit setup documentation**

  Run: `git add .env.example docs/runbooks/import-students-setup.md && git commit -m "docs: add Import Students environment setup"`
