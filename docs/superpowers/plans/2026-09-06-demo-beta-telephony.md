# Demo and Beta Telephony Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Clearly label simulated demo calls and configure Beta to use the existing Twilio provider.

**Architecture:** Keep the existing provider switch. Change only mock-flow copy and Beta environment configuration; do not alter the Twilio Edge Function implementation.

**Tech Stack:** Vite, vanilla JavaScript, Node test runner, Supabase Edge Functions, Twilio.

## Global Constraints

- Automated verification must not initiate a real phone call.
- Demo must remain login-free and mock-backed.
- Beta must use `VITE_TELEPHONY_PROVIDER=twilio`.

---

### Task 1: Lock demo copy with a regression test

**Files:**
- Modify: `tests/app-regression.test.js`
- Modify: `src/app.js`
- Modify: `src/styles.css`

**Interfaces:**
- Consumes: existing mock outcome modal.
- Produces: explicit `Demo simulation` copy without a fabricated duration.

- [ ] Add a source-contract test requiring `Demo simulation` and rejecting `7m 43s` in the mock call workflow.
- [ ] Run the focused test and confirm it fails for the old fixed-duration copy.
- [ ] Replace the fixed-duration copy in the outcome modal and connected detail badge.
- [ ] Run the focused test and confirm it passes.

### Task 2: Enable the Beta Twilio build

**Files:**
- Modify: `.env.beta.local`
- Test: `tests/app-config.test.js`

**Interfaces:**
- Consumes: `VITE_TELEPHONY_PROVIDER` read by `src/lib/telephony.js`.
- Produces: a Beta build where `TELEPHONY_PROVIDER === 'twilio'`.

- [ ] Add a configuration assertion that the Beta environment selects `twilio`.
- [ ] Set `VITE_TELEPHONY_PROVIDER=twilio` in the Beta environment file.
- [ ] Build with `vite build --mode beta` and inspect the bundled provider selection without initiating a call.

### Task 3: Verify and deploy safely

**Files:**
- No source files beyond Tasks 1–2.

**Interfaces:**
- Consumes: passing tests and demo/Beta builds.
- Produces: updated Demo and Beta deployments.

- [ ] Run `npm test`, `npm run build -- --mode demo`, `npm run build -- --mode beta`, and `git diff --check`.
- [ ] Verify required Twilio Edge Functions and server-side secret names without printing secret values.
- [ ] Deploy Demo and Beta with their respective environment modes.
- [ ] Confirm Demo shows simulation copy and Beta follows the real-call branch without placing a call.
