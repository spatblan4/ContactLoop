import test from 'node:test';
import assert from 'node:assert/strict';
import { formatDashboardDate } from '../src/lib/date-labels.js';

test('dashboard date is derived from the current date', () => {
  assert.equal(formatDashboardDate(new Date(2026, 7, 26, 12, 0, 0)), 'Wednesday, August 26, 2026');
});
