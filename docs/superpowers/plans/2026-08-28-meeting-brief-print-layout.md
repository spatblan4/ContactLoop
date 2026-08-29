# Meeting Brief Print Layout Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make printed and PDF meeting briefs retain the desktop presentation layout instead of collapsing into a narrow column.

**Architecture:** Keep the existing meeting brief markup and screen layout. Add narrowly scoped print rules that reset the app shell to one column, override mobile column reductions, and preserve paper-friendly spacing and pagination.

**Tech Stack:** Vanilla JavaScript, CSS, Vite, Node test runner, Playwright CLI.

## Global Constraints

- Brief data generation and screen layout remain unchanged.
- Printed output uses the existing brief DOM and content.
- Detailed contact history starts on a new page.
- Avoid splitting individual brief sections when possible.

---

### Task 1: Add print layout regression coverage

**Files:**
- Modify: `tests/meeting-brief.test.js`
- Modify: `src/styles.css`

**Interfaces:**
- The test suite consumes the generated CSS text and asserts the print contract.
- The print rules produce a single-column `.app-shell`, full-width `.main`, desktop brief column counts, and printable page margins.

- [ ] **Step 1: Write the failing test**

Add a focused assertion to `tests/meeting-brief.test.js` that reads `src/styles.css` and checks the print block contains the required selectors and declarations:

```js
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const styles = fs.readFileSync(path.join(here, '../src/styles.css'), 'utf8');

test('print styles keep meeting brief in a full-width desktop layout', () => {
  const printBlock = styles.slice(styles.lastIndexOf('@page'));

  assert.match(printBlock, /\.app-shell\s*\{[^}]*grid-template-columns:\s*1fr/s);
  assert.match(printBlock, /\.main\s*\{[^}]*width:\s*100%/s);
  assert.match(printBlock, /\.brief-info-grid\s*\{[^}]*grid-template-columns:\s*repeat\(4,1fr\)/s);
  assert.match(printBlock, /\.overview-grid\s*\{[^}]*grid-template-columns:\s*repeat\(6,1fr\)/s);
  assert.match(printBlock, /\.brief-columns\s*\{[^}]*grid-template-columns:\s*1fr\s+1fr/s);
  assert.match(printBlock, /@page\s*\{[^}]*margin:/s);
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node --test tests/meeting-brief.test.js`

Expected: FAIL because the current print block does not reset `.app-shell`, define full-width `.main`, restore desktop column counts, or define `@page` margins.

- [ ] **Step 3: Write minimal implementation**

Replace the existing print block in `src/styles.css` with the same existing declarations plus these print-only declarations:

```css
@page { margin: 0.55in; }
@media print {
  .app-shell { display:block; min-height:0; }
  .main { width:100%; padding:0!important; }
  .meeting-brief-document { width:100%; max-width:none; margin:0; padding:0; border:0; box-shadow:none; }
  .brief-info-grid { grid-template-columns:repeat(4,1fr); }
  .overview-grid { grid-template-columns:repeat(6,1fr); }
  .brief-columns { grid-template-columns:1fr 1fr; gap:24px; }
  .brief-header { display:flex; }
  .brief-meta { text-align:right; margin-top:0; }
}
```

Keep the existing toolbar/sidebar hiding, section break avoidance, history page break, and print border overrides in the same block.

- [ ] **Step 4: Run test to verify it passes**

Run: `node --test tests/meeting-brief.test.js`

Expected: PASS with all meeting brief tests passing.

### Task 2: Verify the rendered print layout

**Files:**
- Inspect: `src/app.js:167,217`
- Inspect: `src/styles.css:211-217`

**Interfaces:**
- The existing `data-action="print-brief"` handler calls `window.print()`.
- The browser applies the `print` media rules to the rendered `.meeting-brief-document`.

- [ ] **Step 1: Run the complete test suite**

Run: `npm test`

Expected: exit code 0 and all tests pass.

- [ ] **Step 2: Start the local app**

Run: `npm run dev -- --host 127.0.0.1`

Expected: Vite serves the app on a local URL, typically `http://127.0.0.1:5173`.

- [ ] **Step 3: Inspect print media with Playwright**

Open the local app with the existing browser automation and evaluate the print stylesheet contract. Confirm computed print styles report:

```js
{
  shellColumns: '1fr',
  mainWidth: '100%',
  infoColumns: 'repeat(4, 1fr)',
  overviewColumns: 'repeat(6, 1fr)',
  briefColumns: '1fr 1fr'
}
```

Expected: the meeting brief occupies the printable page width, the desktop column counts remain active, and the toolbar/sidebar are hidden in print.

- [ ] **Step 4: Stop the dev server and record the result**

Use the browser snapshot/evaluation output plus the test output as verification evidence. If browser automation cannot reach the demo screen because authentication or data setup blocks it, report that limitation and retain the automated CSS regression result.
