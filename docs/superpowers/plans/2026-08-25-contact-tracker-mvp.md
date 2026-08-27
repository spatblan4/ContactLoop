# NoteLess EDU Contact Tracker MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an English, clickable MVP demo that automatically turns mock phone outcomes into contact history, dashboard metrics, and follow-up state.

**Architecture:** A dependency-light browser app with a single state store in `src/app.js`, semantic page shells in `index.html`, and a focused visual system in `src/styles.css`. Mock call events use the same fields the future Supabase/Twilio backend will need, while provider integration remains out of scope.

**Tech Stack:** HTML, CSS, modern browser JavaScript, Vite for local serving, Playwright CLI for smoke verification.

## Global Constraints

- All user-facing copy is English.
- Do not record audio, transcribe calls, or make compliance claims.
- Mock call outcomes must include Connected, No Answer, Busy, and Failed.
- A saved event must update dashboard counts, student history, and follow-up visibility.
- AI behavior is simulated only through an explicitly teacher-confirmed note flow.

---

### Task 1: Create the browser app shell and visual system

**Files:**
- Create: `package.json`
- Create: `index.html`
- Create: `src/styles.css`
- Create: `src/app.js`

**Interfaces:**
- `render()` owns the current screen and app chrome.
- `state` owns students, contact events, follow-ups, and the active screen.
- `createContactEvent(input)` returns a persisted contact event with `attemptNumber` derived from prior student events.

- [ ] **Step 1: Add the Vite start script and app entry point.**
- [ ] **Step 2: Add the semantic app shell with sidebar, dashboard root, and modal root.**
- [ ] **Step 3: Add CSS variables, typography, cards, navigation, tables, badges, responsive behavior, and staggered entrance animations.**
- [ ] **Step 4: Add seeded student/contact data and render the dashboard, student list, follow-ups, and contact log.**
- [ ] **Step 5: Run `npm install` and `npm run dev -- --host 127.0.0.1` to confirm the shell serves.

### Task 2: Implement the end-to-end call workflow

**Files:**
- Modify: `src/app.js`
- Modify: `src/styles.css`

**Interfaces:**
- `openCallFlow(studentId)` opens the call modal.
- `completeMockCall(result)` creates an event for the selected student.
- `openStudentDetail(studentId)` renders contact history and follow-up context.

- [ ] **Step 1: Add student cards with `Call` actions and route-like screen state.**
- [ ] **Step 2: Add a mock call modal with Connected, No Answer, Busy, and Failed outcomes.**
- [ ] **Step 3: After Connected, show topic chips and an optional teacher note; after unsuccessful outcomes, offer a follow-up selector.**
- [ ] **Step 4: Persist the event and re-render metrics, activity, student history, and attention items without a page reload.**
- [ ] **Step 5: Add the Emma No Answer → Attempt #2 and Lucas Connected → IEP demo paths.**

### Task 3: Verify the MVP behavior and responsive presentation

**Files:**
- Modify: `src/app.js` only if smoke checks expose a behavior issue.
- Modify: `src/styles.css` only if smoke checks expose a layout issue.

- [ ] **Step 1: Use Playwright CLI to load the app and snapshot the dashboard.**
- [ ] **Step 2: Click Emma's call action, choose No Answer, save, and verify `Attempt #2` and updated dashboard metrics appear.**
- [ ] **Step 3: Click Lucas's call action, choose Connected, choose IEP, save, and verify the event appears in recent activity and history.**
- [ ] **Step 4: Check the mobile breakpoint and ensure the primary call flow remains usable.**
- [ ] **Step 5: Run a production build and inspect the final diff before reporting results.
