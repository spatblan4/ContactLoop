import test from 'node:test';
import assert from 'node:assert/strict';
import { shouldUseOwnerDerivedStudentInsert } from '../src/lib/supabase.js';

test('a signed-in teacher uses the owner-derived student import even if demo mode is stale', () => {
  assert.equal(shouldUseOwnerDerivedStudentInsert({ appMode: 'demo', session: { user: { id: 'teacher-1' } } }), true);
});

test('a signed-out demo keeps the legacy demo insert path', () => {
  assert.equal(shouldUseOwnerDerivedStudentInsert({ appMode: 'demo', session: null }), false);
});
