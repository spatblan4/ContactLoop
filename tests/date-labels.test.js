import test from 'node:test';
import assert from 'node:assert/strict';
import { formatDashboardDate } from '../src/lib/date-labels.js';

test('dashboard date is derived from the current date', () => {
  assert.equal(formatDashboardDate(new Date('2026-08-26T12:00:00-07:00')), 'Wednesday, August 26, 2026');
});
