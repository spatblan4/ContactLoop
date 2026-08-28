import test from 'node:test';
import assert from 'node:assert/strict';
import { parseFollowUpDate } from '../src/lib/followup-date.js';

test('parseFollowUpDate accepts a calendar date and fixes the follow-up time', () => {
  assert.equal(parseFollowUpDate('2026-08-27'), '2026-08-27T16:00:00.000Z');
});

test('parseFollowUpDate rejects malformed and impossible dates', () => {
  assert.equal(parseFollowUpDate(''), null);
  assert.equal(parseFollowUpDate('08/27/2026'), null);
  assert.equal(parseFollowUpDate('2026-02-31'), null);
});
