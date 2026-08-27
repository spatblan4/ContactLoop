import assert from 'node:assert/strict';
import test from 'node:test';

const eventModuleUrl = new URL('../src/lib/contact-events.js', import.meta.url);

test('contact events are ordered by call time instead of random UUID', async () => {
  const { newestContactEventsFirst = events => events } = await import(eventModuleUrl).catch(() => ({}));
  const events = [
    { id: 'z-old', callTime: '2026-08-25T10:00:00.000Z' },
    { id: 'a-new', callTime: '2026-08-25T12:00:00.000Z' },
    { id: 'm-middle', callTime: '2026-08-25T11:00:00.000Z' },
  ];

  assert.deepEqual(newestContactEventsFirst(events).map(event => event.id), [
    'a-new',
    'm-middle',
    'z-old',
  ]);
  assert.deepEqual(events.map(event => event.id), ['z-old', 'a-new', 'm-middle']);
});

test('short call durations are displayed in seconds', async () => {
  const { formatCallDuration = () => null } = await import(eventModuleUrl).catch(() => ({}));

  assert.equal(formatCallDuration(19), '19 sec');
  assert.equal(formatCallDuration(78), '1m 18s');
  assert.equal(formatCallDuration(null), null);
});
