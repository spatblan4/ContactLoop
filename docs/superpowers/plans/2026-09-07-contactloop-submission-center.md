# ContactLoop Submission Center Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a standalone ContactLoop submission dashboard containing an evidence-based persistent checklist and three complete collapsible AWS Builder articles.

**Architecture:** A single self-contained HTML file owns presentation, checklist seed data, local persistence, progress calculation, article accordions, and clipboard behavior. A Node source-contract test verifies required content and interaction hooks; the verified HTML is then copied byte-for-byte from `docs/` to `public/`.

**Tech Stack:** Semantic HTML5, embedded CSS, vanilla JavaScript, Node.js test runner, localStorage, Clipboard API.

## Global Constraints

- The page must work from the local filesystem without a framework, build step, external font, or network request.
- Only repository-verified items begin checked; account, upload, publication, deployment, and Devpost actions remain unchecked.
- Saved checkbox state uses the versioned key `contactloop-submission-center-v1`.
- Every checkbox has a visible label and a stable `data-check-id`.
- Progress shows both a percentage and completed-versus-total count.
- The reset action requires confirmation.
- All three full article drafts are embedded and independently collapsible.
- Copy feedback is inline and includes a fallback when the Clipboard API is unavailable.
- No private student data, phone numbers, credentials, secrets, or service keys are embedded.
- `docs/contactloop-submission-center.html` and `public/contactloop-submission-center.html` must be identical.

---

### Task 1: Lock the Submission Center Contract

**Files:**
- Create: `tests/submission-center.test.js`
- Test: `tests/submission-center.test.js`

**Interfaces:**
- Consumes: the paths `docs/contactloop-submission-center.html` and `public/contactloop-submission-center.html`.
- Produces: Node tests that verify HTML structure, checklist groups, persistence hooks, article titles, control labels, and identical public/docs copies.

- [ ] **Step 1: Write the failing contract tests**

Create tests that read both HTML files and assert:

```js
assert.match(html, /contactloop-submission-center-v1/);
assert.match(html, /data-check-group="accounts"/);
assert.match(html, /data-check-group="product"/);
assert.match(html, /data-check-group="technical"/);
assert.match(html, /data-check-group="repository"/);
assert.match(html, /data-check-group="devpost"/);
assert.match(html, /data-check-group="video"/);
assert.match(html, /data-check-group="articles"/);
assert.match(html, /Agents for Humans: Why I Built ContactLoop/);
assert.match(html, /Agents for Humans: Building ContactLoop/);
assert.match(html, /Agents for Humans: AI Should Prepare the Record/);
assert.match(html, /id="expandAll"/);
assert.match(html, /id="collapseAll"/);
assert.match(html, /id="resetProgress"/);
assert.match(html, /navigator\.clipboard/);
assert.equal(publicHtml, html);
```

- [ ] **Step 2: Run the test and verify it fails**

Run `node --test tests/submission-center.test.js`.

Expected: failure because the two HTML files do not exist.

- [ ] **Step 3: Commit the failing test**

```bash
git add tests/submission-center.test.js
git commit -m "test: define submission center contract"
```

### Task 2: Build the Checklist Dashboard

**Files:**
- Create: `docs/contactloop-submission-center.html`
- Test: `tests/submission-center.test.js`

**Interfaces:**
- Consumes: checklist groups and default states defined in `docs/superpowers/specs/2026-09-06-contactloop-submission-center-design.md`.
- Produces: a self-contained HTML dashboard with semantic checklist markup and the JavaScript functions `loadSavedState()`, `saveState()`, `updateProgress()`, and `resetProgress()`.

- [ ] **Step 1: Create semantic page structure**

Add a hero, deadline block, progress block, seven grouped checklist sections, readiness summary, article-library heading, and footer. Use `<main>`, `<header>`, `<section>`, headings in order, native checkboxes, and visible labels.

- [ ] **Step 2: Add evidence-based default checklist states**

Mark repository-supported product and writing tasks with `checked`. Leave external account, AgentCore, live-demo verification, repository compliance, Devpost, recording/upload, screenshot, and publication tasks unchecked.

- [ ] **Step 3: Add progress persistence**

Implement `loadSavedState()` to accept only an object of boolean values, `saveState()` inside `try/catch`, and `updateProgress()` from the currently checked controls. Attach change listeners by stable `data-check-id` values.

- [ ] **Step 4: Add confirmed reset behavior**

The `resetProgress` button calls `window.confirm('恢复为证据核验后的默认状态？你手动保存的勾选进度会被覆盖。')`. On confirmation, clear the versioned key, restore every checkbox's `data-default-checked` value, and update progress.

- [ ] **Step 5: Add the editorial visual system**

Use CSS variables for warm paper, deep forest ink, chartreuse completion, and amber pending states. Use Georgia for display/body editorial text and Trebuchet MS/monospace for controls and metadata. Include responsive layouts, visible focus styles, a subtle CSS grid/grain background, short reveal motion, and a reduced-motion override.

### Task 3: Embed the Article Library

**Files:**
- Modify: `docs/contactloop-submission-center.html`
- Read: `docs/builder-articles/01-why-i-built-contactloop.md`
- Read: `docs/builder-articles/02-building-contactloop.md`
- Read: `docs/builder-articles/03-ai-and-teacher-judgment.md`
- Test: `tests/submission-center.test.js`

**Interfaces:**
- Consumes: exact published draft content from the three Markdown source files.
- Produces: three `<details class="article-card">` elements and the functions `setAllArticles(open)` and `copyArticle(button)`.

- [ ] **Step 1: Render each full article as semantic HTML**

Convert Markdown headings, paragraphs, lists, block quotes, code blocks, emphasis, and links to static HTML without truncating or rewriting the source content. Place each article in its own `<details>` element.

- [ ] **Step 2: Add article metadata**

Show article number, exact title, verified word count, and `Draft ready` status in every summary row.

- [ ] **Step 3: Add expansion controls**

The `expandAll` and `collapseAll` buttons call `setAllArticles(true)` and `setAllArticles(false)` respectively. The function sets the native `open` property on all `.article-card` elements.

- [ ] **Step 4: Add copy controls with fallback**

Each article body has a `data-copy-source` identifier. `copyArticle(button)` copies `innerText` through `navigator.clipboard.writeText`. If unavailable or rejected, create an off-screen textarea, use `document.execCommand('copy')`, remove the textarea, and show inline success or manual-selection feedback.

### Task 4: Publish the Identical Static Copy and Verify

**Files:**
- Create: `public/contactloop-submission-center.html`
- Test: `tests/submission-center.test.js`

**Interfaces:**
- Consumes: completed `docs/contactloop-submission-center.html`.
- Produces: an identical public copy and full verification evidence.

- [ ] **Step 1: Copy the verified HTML mechanically**

Run `cp docs/contactloop-submission-center.html public/contactloop-submission-center.html`.

- [ ] **Step 2: Run the focused contract test**

Run `node --test tests/submission-center.test.js`.

Expected: all submission-center tests pass.

- [ ] **Step 3: Run the full project tests and build**

Run `npm test`, then run `npm run build`.

Expected: 0 test failures and a successful Vite production build; the existing bundle-size warning is acceptable.

- [ ] **Step 4: Run static integrity checks**

Run `cmp docs/contactloop-submission-center.html public/contactloop-submission-center.html`, then run `git diff --check -- docs/contactloop-submission-center.html public/contactloop-submission-center.html tests/submission-center.test.js`.

Expected: `cmp` exits 0 with no output and `git diff --check` reports no whitespace errors.

- [ ] **Step 5: Verify the page in a browser**

Open the public route, test a checkbox reload cycle, reset, expand all, collapse all, copy each article, and inspect desktop and mobile widths. Confirm there are no console errors.

- [ ] **Step 6: Commit the completed submission center**

```bash
git add docs/contactloop-submission-center.html public/contactloop-submission-center.html tests/submission-center.test.js
git commit -m "feat: add ContactLoop submission center"
```
