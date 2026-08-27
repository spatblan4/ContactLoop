import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';

const migrationPath = new URL('../supabase/patch-import-students-auth.sql', import.meta.url);

test('auth migration defines teacher ownership and import columns', () => {
  const sql = fs.readFileSync(migrationPath, 'utf8');
  assert.match(sql, /add column if not exists teacher_id uuid/i);
  assert.match(sql, /add column if not exists first_name text/i);
  assert.match(sql, /add column if not exists last_name text/i);
  assert.match(sql, /add column if not exists email text/i);
});

test('auth migration removes anonymous policies and adds auth uid ownership checks', () => {
  const sql = fs.readFileSync(migrationPath, 'utf8');
  assert.match(sql, /drop policy if exists .*demo/i);
  assert.match(sql, /to authenticated/i);
  assert.match(sql, /auth\.uid\(\)/i);
  assert.doesNotMatch(sql, /to anon\s+using\s*\(true\)/i);
});

test('import RPC derives owner from auth uid and returns import counts', () => {
  const sql = fs.readFileSync(migrationPath, 'utf8');
  assert.match(sql, /create or replace function public\.import_students/i);
  assert.match(sql, /p_students jsonb,\s*p_guardians jsonb/i);
  assert.match(sql, /teacher_id\s*=\s*auth\.uid\(\)/i);
  assert.match(sql, /students_imported/i);
  assert.match(sql, /guardians_imported/i);
  assert.doesNotMatch(sql, /p_teacher_id/i);
});
