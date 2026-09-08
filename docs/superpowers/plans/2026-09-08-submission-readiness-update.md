# ContactLoop Submission Readiness Update Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce the missing repository submission materials and update the evidence-backed HTML progress from 19/54 to 26/54.

**Architecture:** Keep public-facing facts in focused Markdown files and treat the HTML as generated output. Contract tests verify required sections, safe disclosure language, completion defaults, and storage-version migration.

**Tech Stack:** Markdown, Node.js built-in test runner, JavaScript HTML generator, static HTML/CSS/JavaScript.

## Global Constraints

- Do not mark external platform actions complete without direct evidence.
- Do not include credentials, real student information, or guardian-call recording claims.
- Preserve unrelated working-tree changes.

---

### Task 1: Define the documentation contract

**Files:**
- Create: `tests/submission-readiness.test.js`
- Modify: `tests/submission-center.test.js`

- [ ] Add assertions for README sections, MIT license, Devpost fields, privacy results, v2 persistence, seven new checked defaults, and 26/54 total defaults.
- [ ] Run `node --test tests/submission-readiness.test.js tests/submission-center.test.js` and confirm it fails because the artifacts and v2 output do not exist yet.

### Task 2: Create submission-ready repository documents

**Files:**
- Modify: `README.md`
- Create: `LICENSE`
- Create: `docs/devpost-submission.md`
- Create: `docs/submission/privacy-scan.md`

- [ ] Write the public README using verified architecture, commands, environment variable names, test instructions, safety boundaries, and dated work disclosure.
- [ ] Add the standard MIT license with `Copyright (c) 2026 ContactLoop contributors`.
- [ ] Write the Devpost draft under the standard headings: Inspiration, What it does, How we built it, Challenges, Accomplishments, What we learned, and What's next.
- [ ] Run filename-only scans for tracked environment files and high-confidence credential patterns, then record the commands, results, date, and limitations.
- [ ] Run the focused documentation test and confirm it passes.

### Task 3: Update the submission center

**Files:**
- Modify: `scripts/generate-submission-center.mjs`
- Modify: `docs/contactloop-submission-center.html`
- Modify: `public/contactloop-submission-center.html`

- [ ] Mark only the seven newly evidenced items complete and link their notes to repository paths.
- [ ] Change the persistence key to `contactloop-submission-center-v2` and the page update date to 2026-09-08.
- [ ] Run `node scripts/generate-submission-center.mjs`.
- [ ] Run the focused tests and confirm the page reports 26 checked defaults out of 54.

### Task 4: Verify the complete deliverable

**Files:**
- Verify all files above.

- [ ] Run `npm test` and require zero failures.
- [ ] Run `npm run build` and require exit code zero.
- [ ] Open `public/contactloop-submission-center.html` in a browser; verify 26/54, 48%, functional article controls, and zero console errors.
- [ ] Review `git diff --check` and the scoped diff before committing only task-owned files.

