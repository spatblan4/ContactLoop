# Meeting Brief Teacher Notes Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Include confirmed typed and voice teacher notes from Supabase in Meeting Brief generation without changing telephony or AI provider behavior.

**Architecture:** Pass the already-loaded `state.teacherNotes` into the existing deterministic `buildMeetingBrief` function. The builder filters notes by student, reporting range, and `teacher_confirmed`, then merges their text with event notes for concerns and agreements and exposes the notes in the detailed history section. No new table or API is required.

**Tech Stack:** Vanilla JavaScript, Supabase-loaded workspace state, Node built-in test runner, Vite.

## Global Constraints

- Only teacher-confirmed notes are eligible for Meeting Brief output.
- Notes are scoped to the selected student and date range.
- Existing contact-event statistics remain deterministic and unchanged.
- Do not change Twilio, AI provider, voice upload, or Supabase schema behavior.
- Do not expose phone numbers, provider IDs, or raw audio data in the brief.

---

### Task 1: Add failing Meeting Brief note-inclusion tests

**Files:**
- Modify: `tests/meeting-brief.test.js`
- Modify: `src/lib/meeting-brief.js`

**Interfaces:**
- `buildMeetingBrief({ events, students, followUps, teacherNotes, studentId, range, now })` accepts optional `teacherNotes` and returns `teacherNotes` in the brief plus merged note-derived concerns and agreements.

- [ ] **Step 1: Write the failing tests**

Add a confirmed typed note, a confirmed voice note, an unconfirmed note, an unrelated-student note, and an out-of-range note. Assert only the two eligible notes appear in the brief and that the existing event totals are unchanged.

```js
test('meeting brief includes confirmed teacher notes for the selected student and range', () => {
  const teacherNotes = [
    { id: 'n1', student_id: 'emma', content: 'Parent requested transportation information.', source: 'typed', teacher_confirmed: true, created_at: '2026-08-24T10:00:00-07:00' },
    { id: 'n2', student_id: 'emma', content: 'Family agreed to practice reading at home.', source: 'voice', teacher_confirmed: true, created_at: '2026-08-25T15:00:00-07:00' },
    { id: 'n3', student_id: 'emma', content: 'Do not include this unconfirmed note.', source: 'voice', teacher_confirmed: false, created_at: '2026-08-25T16:00:00-07:00' },
    { id: 'n4', student_id: 'lucas', content: 'Other student note.', source: 'typed', teacher_confirmed: true, created_at: '2026-08-25T16:00:00-07:00' },
    { id: 'n5', student_id: 'emma', content: 'Older note outside the selected range.', source: 'typed', teacher_confirmed: true, created_at: '2026-07-25T16:00:00-07:00' },
  ];
  const brief = buildMeetingBrief({ events, students, followUps: [], teacherNotes, studentId: 'emma', range: { preset: 'this-month' }, now });
  assert.deepEqual(brief.teacherNotes.map(note => note.content), [teacherNotes[1].content, teacherNotes[0].content]);
  assert.match(brief.concerns.join(' '), /transportation/);
  assert.match(brief.agreements.join(' '), /practice reading/);
  assert.equal(brief.overview.totalAttempts, 2);
});

test('meeting brief detailed history exposes confirmed teacher notes separately from event notes', () => {
  const brief = buildMeetingBrief({
    events,
    students,
    followUps: [],
    teacherNotes: [{ id: 'n1', student_id: 'emma', content: 'Parent requested transportation information.', source: 'typed', teacher_confirmed: true, created_at: '2026-08-24T10:00:00-07:00' }],
    studentId: 'emma',
    range: { preset: 'this-month' },
    now,
  });
  assert.equal(brief.detailedHistory.some(item => item.teacherNote === 'Parent requested transportation information.'), true);
  assert.equal(brief.detailedHistory.some(item => item.source === 'typed'), true);
});
```

- [ ] **Step 2: Run the focused tests and verify they fail for the missing behavior**

Run:

```bash
node --test tests/meeting-brief.test.js
```

Expected: the two new tests fail because `teacherNotes` is not yet accepted or included.

- [ ] **Step 3: Implement the minimal builder changes**

Update `buildMeetingBrief` to accept `teacherNotes = []`, filter confirmed notes using the existing date-range bounds, merge their content with eligible event notes for `noteSections`, and append note-only entries to `detailedHistory` with `teacherNote`, `source`, and display time. Keep event statistics and event-only fields unchanged.

- [ ] **Step 4: Run the focused tests and verify they pass**

Run:

```bash
node --test tests/meeting-brief.test.js
```

Expected: all Meeting Brief tests pass.

- [ ] **Step 5: Commit the isolated logic change**

```bash
git add tests/meeting-brief.test.js src/lib/meeting-brief.js
git commit -m "feat: include confirmed teacher notes in meeting briefs"
```

### Task 2: Wire application state into Meeting Brief generation

**Files:**
- Modify: `src/app.js:154`
- Test: `tests/meeting-brief.test.js`

**Interfaces:**
- `generateMeetingBrief()` passes `state.teacherNotes` to `buildMeetingBrief`.

- [ ] **Step 1: Add an application-level source assertion**

Keep the behavior covered through the pure builder test and add the `teacherNotes: state.teacherNotes` argument in the existing `generateMeetingBrief` call.

- [ ] **Step 2: Run the full test suite**

Run:

```bash
node --test tests/*.test.js
```

Expected: all tests pass with zero failures.

- [ ] **Step 3: Build the application**

Run:

```bash
npm run build
```

Expected: Vite exits with code 0 and produces the `dist` output.

- [ ] **Step 4: Commit the application wiring**

```bash
git add src/app.js
git commit -m "feat: wire teacher notes into meeting brief generation"
```

## Self-review checklist

- Confirmed notes are filtered by student, date range, and `teacher_confirmed`.
- Typed and voice notes use the same `teacher_notes` source.
- Event counts remain based only on final contact events.
- Meeting Brief can show note-only context without inventing a call event.
- Existing phone/provider privacy filtering remains intact.
