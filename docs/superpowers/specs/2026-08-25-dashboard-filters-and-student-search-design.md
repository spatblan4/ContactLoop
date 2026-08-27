# Dashboard Filters and Student Search Design

## Goal

Make ContactLoop easier to review over time and easier to navigate by adding a Dashboard date range filter and live search on the Students page.

## Approved behavior

### Dashboard date filter

The Dashboard defaults to `Today`. The selector offers:

- Today
- Yesterday
- This week
- This month
- This year
- Custom date range

The selected range filters the top metrics, Needs attention, Contact pulse, and Recent activity. `Calls` counts only final outcomes (`Connected`, `No Answer`, `Busy`, `Failed`); pending states such as `Initiated` and `Ringing` remain in history but do not affect the total.

For custom range, the UI uses two native date inputs (`From` and `To`) and includes both endpoints. The range is local-calendar based, matching the existing Dashboard date display.

### Students search

The Students page gets a search input below the page heading and above the cards. It filters immediately, case-insensitively, across student name, guardian name, and phone number. The `+ Add student` action remains in the page header. Empty results show `No students match your search.`

## Data flow

Supabase remains the source of truth. No new database tables or columns are needed. The existing normalized event data gains a stable local date value used by the Dashboard filter. Filtering happens in the client after the existing Supabase query, so search and date changes are instant and do not create extra network requests.

## Interaction and error behavior

- The default filter is Today after a page load or refresh.
- Changing the date range immediately recalculates metrics and visible activity.
- Custom range requires both dates and rejects a `From` date after `To` with an inline message.
- Clearing Students search restores all cards.
- Search and filter state are local UI state only and reset on refresh.

## Testing

- Unit test date preset boundaries and inclusive custom ranges.
- Unit test that pending calls are excluded and final outcome counts sum to `Calls`.
- Unit test student search matching student, guardian, and phone values, plus empty results.
- Run the full Node test suite, production build, and browser verification for Today, Custom range, and Students search.
