# Meeting Brief Print Layout Design

## Goal

Make printed and PDF versions of the AI-generated meeting brief preserve the desktop presentation layout instead of collapsing into a narrow column.

## Root cause

The brief is rendered inside `.app-shell`, which keeps its two-column grid (`sidebar` plus `main`) when the sidebar is hidden by `@media print`. The remaining main grid track therefore does not receive the full paper width. The existing mobile breakpoint can also apply during narrow print layout and reduce the brief's columns.

## Design

Keep the existing meeting brief DOM and screen styles. Extend the print media rules only for the print context:

- Make `.app-shell` a single-column layout and let `.main` occupy the full printable width.
- Remove screen spacing, borders, and shadows from the printable document while retaining readable paper padding.
- Preserve desktop brief composition in print: four student-information columns, six overview cards, and two-column brief sections.
- Keep detailed history on a new page and avoid splitting individual brief sections when possible.
- Define page margins and print color behavior so browser print preview and PDF output are consistent across standard paper sizes.

## Scope

Only `src/styles.css` and targeted regression coverage are in scope. Brief data generation, content, and screen layout are unchanged.

## Verification

- Run the existing automated test suite.
- Load the meeting brief in a browser and inspect print media styles.
- Confirm the printable document uses the full paper width, desktop column counts, and the intended history page break.
