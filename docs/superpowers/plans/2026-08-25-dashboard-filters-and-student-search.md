# Dashboard Filters and Student Search Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add local date-range filtering to the Dashboard and live search to the Students page while preserving Supabase as the source of truth.

**Architecture:** Add small pure helpers for date ranges and student matching. Keep UI state in `src/app.js`; apply the selected Dashboard range to normalized events before deriving metrics and activity, and apply the Students query before rendering cards. No schema or Edge Function changes are required.

**Tech Stack:** Vanilla JavaScript modules, Supabase data layer, Vite, Node test runner.

## Global Constraints

- Dashboard defaults to `Today`.
- Final call results are `Connected`, `No Answer`, `Busy`, and `Failed`.
- `Initiated` and `Ringing` remain visible in history but are excluded from `Calls`.
- Date ranges use the browser's local calendar and include both custom endpoints.
- Students search is case-insensitive across student name, guardian name, and phone.
- No new database tables, columns, or network requests are added.

### Task 1: Add tested date-range filtering

**Files:**
- Create: `src/lib/date-filters.js`
- Test: `tests/date-filters.test.js`

**Interfaces:**
- Produces `filterEventsByRange(events, range, now)` where `range` is `{ preset, from, to }` and the return value is a new event array.
- Produces `rangeLabel(range, now)` for the Dashboard control label.

- [ ] **Step 1: Write the failing tests**

Test Today, This week, and inclusive custom dates with events on boundaries and outside the range.

- [ ] **Step 2: Run the date-filter test and verify it fails**

Run: `node --test tests/date-filters.test.js`

Expected: FAIL because `src/lib/date-filters.js` does not yet export the requested helpers.

- [ ] **Step 3: Implement the minimal date helpers**

Use local midnight boundaries. Presets produce a start and end date; custom dates use the supplied local dates and include the entire `to` day.

- [ ] **Step 4: Run the date-filter test and verify it passes**

Run: `node --test tests/date-filters.test.js`

Expected: PASS.

- [ ] **Step 5: Commit the tested helper**

Run: `git add src/lib/date-filters.js tests/date-filters.test.js && git commit -m "feat: add dashboard date range helpers"`.

### Task 2: Add tested Student search matching

**Files:**
- Create: `src/lib/student-search.js`
- Test: `tests/student-search.test.js`

**Interfaces:**
- Produces `filterStudents(students, query)` and returns a new array.
- It matches `name`, `parent`, `relation`, and `phone` case-insensitively after trimming the query.

- [ ] **Step 1: Write the failing tests**

Cover student-name, guardian-name, phone-number matches, empty query returning all students, and no-match returning an empty array.

- [ ] **Step 2: Run the Student search test and verify it fails**

Run: `node --test tests/student-search.test.js`

Expected: FAIL because `src/lib/student-search.js` does not yet export `filterStudents`.

- [ ] **Step 3: Implement the minimal search helper**

Normalize the query and searchable fields with `String(value ?? '').toLowerCase()` and use `includes`.

- [ ] **Step 4: Run the Student search test and verify it passes**

Run: `node --test tests/student-search.test.js`

Expected: PASS.

- [ ] **Step 5: Commit the tested helper**

Run: `git add src/lib/student-search.js tests/student-search.test.js && git commit -m "feat: add student search matching"`.

### Task 3: Connect Dashboard date controls

**Files:**
- Modify: `src/app.js`
- Modify: `src/styles.css`
- Test: `tests/dashboard-stats.test.js`

**Interfaces:**
- App state stores `dashboardRange` initialized to `{ preset: 'today', from: '', to: '' }`.
- Dashboard renders a range selector and custom From/To controls.
- The filtered event list is used by `dashboardTotals`, `Needs attention`, `Contact pulse`, and `Recent activity`.

- [ ] **Step 1: Extend the stats test with range-scoped totals**

Assert that final results outside the selected range do not affect `Calls` or outcome cards, while pending results remain excluded inside the range.

- [ ] **Step 2: Run the stats test and verify the new assertion fails**

Run: `node --test tests/dashboard-stats.test.js`

Expected: FAIL because Dashboard totals currently always use `dateKey === 'today'`.

- [ ] **Step 3: Implement the Dashboard state and filtering**

Import the date helper, derive `filteredEvents` from `state.events`, pass it to `dashboardTotals`, and render a compact control beside the Dashboard heading. Re-render on preset changes. Show two date inputs only for Custom and show an inline validation message when From is after To.

- [ ] **Step 4: Update Dashboard sections to use the filtered events**

Use the same filtered array for Needs attention, Contact pulse, and Recent activity so every visible Dashboard section follows the selected range.

- [ ] **Step 5: Add CSS for the selector and custom date controls**

Match the existing ContactLoop controls with a bordered compact select, accessible labels, and a responsive layout that stacks below the heading on narrow screens.

- [ ] **Step 6: Run the full test suite and build**

Run: `node --test tests/*.test.js && npm run build && git diff --check`

Expected: all tests pass, Vite build succeeds, and `git diff --check` prints no errors.

- [ ] **Step 7: Commit the Dashboard filter**

Run: `git add src/app.js src/styles.css tests/dashboard-stats.test.js && git commit -m "feat: filter dashboard by date range"`.

### Task 4: Connect Students search UI

**Files:**
- Modify: `src/app.js`
- Modify: `src/styles.css`

**Interfaces:**
- App state stores `studentSearch` initialized to an empty string.
- `studentsScreen()` passes `state.students` and `state.studentSearch` through `filterStudents`.
- The search input updates state on input and re-renders the card grid without changing Supabase data.

- [ ] **Step 1: Add the search input and empty state**

Render the search input below the Students heading, preserve `+ Add student` in the header, and render `No students match your search.` when the filtered list is empty.

- [ ] **Step 2: Bind live input behavior**

Use an input listener that updates `state.studentSearch`, preserves the caret, and re-renders only the Students view.

- [ ] **Step 3: Add responsive styling**

Give the input enough width and vertical spacing to match the existing cards, with a full-width layout on small screens.

- [ ] **Step 4: Run the full test suite and build**

Run: `node --test tests/*.test.js && npm run build && git diff --check`

Expected: all tests pass, Vite build succeeds, and `git diff --check` prints no errors.

- [ ] **Step 5: Commit the Students search**

Run: `git add src/app.js src/styles.css && git commit -m "feat: search students by contact details"`.

### Task 5: Browser verification

**Files:**
- Modify: none.

- [ ] **Step 1: Verify Dashboard Today**

Open `http://127.0.0.1:5176/`, enter the Dashboard, select Today, and confirm the cards total equals the sum of final outcome cards.

- [ ] **Step 2: Verify Dashboard Custom range**

Select Custom, set From and To to a known event date, and confirm the metrics and Recent activity change together.

- [ ] **Step 3: Verify Students search**

Open Students, search `Emma`, `Sarah`, and a phone fragment, then clear the input and confirm all students return.

- [ ] **Step 4: Record the verification result**

Run: `node --test tests/*.test.js && npm run build`

Expected: all tests pass and the browser displays the selected-range and search results without console errors.
