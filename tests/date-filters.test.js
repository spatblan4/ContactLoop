import assert from 'node:assert/strict';
import test from 'node:test';

const moduleUrl = new URL('../src/lib/date-filters.js', import.meta.url);

test('date presets include the correct local calendar boundaries', async () => {
  const { filterEventsByRange = () => [] } = await import(moduleUrl).catch(() => ({}));
  const now = new Date(2026, 7, 25, 12, 0, 0);
  const events = [
    { id: 'today-start', callTime: new Date(2026, 7, 25, 0, 0, 0).toISOString() },
    { id: 'today-end', callTime: new Date(2026, 7, 25, 23, 59, 59).toISOString() },
    { id: 'yesterday', callTime: new Date(2026, 7, 24, 12, 0, 0).toISOString() },
    { id: 'last-month', callTime: new Date(2026, 6, 31, 12, 0, 0).toISOString() },
  ];

  assert.deepEqual(filterEventsByRange(events, { preset: 'today' }, now).map(event => event.id), ['today-start', 'today-end']);
  assert.deepEqual(filterEventsByRange(events, { preset: 'yesterday' }, now).map(event => event.id), ['yesterday']);
  assert.deepEqual(filterEventsByRange(events, { preset: 'custom', from: '2026-08-24', to: '2026-08-25' }, now).map(event => event.id), ['today-start', 'today-end', 'yesterday']);
});

test('custom date ranges include both endpoints', async () => {
  const { filterEventsByRange = () => [] } = await import(moduleUrl).catch(() => ({}));
  const events = [
    { id: 'before', callTime: new Date(2026, 7, 24, 23, 59, 59).toISOString() },
    { id: 'from', callTime: new Date(2026, 7, 25, 0, 0, 0).toISOString() },
    { id: 'to', callTime: new Date(2026, 7, 26, 23, 59, 59).toISOString() },
    { id: 'after', callTime: new Date(2026, 7, 27, 0, 0, 0).toISOString() },
  ];

  assert.deepEqual(filterEventsByRange(events, { preset: 'custom', from: '2026-08-25', to: '2026-08-26' }).map(event => event.id), ['from', 'to']);
});
