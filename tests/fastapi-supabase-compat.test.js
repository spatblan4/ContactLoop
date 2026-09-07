import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';

const migrationPath = new URL('../supabase/patch-fastapi-supabase-compat.sql', import.meta.url);

function readMigration() {
  return fs.readFileSync(migrationPath, 'utf8');
}

test('FastAPI compatibility migration is additive and preserves Agent tables', () => {
  const sql = readMigration();

  assert.doesNotMatch(sql, /\bdrop\s+table\b/i);
  assert.doesNotMatch(sql, /\bdrop\s+column\b/i);
  assert.doesNotMatch(sql, /\bdelete\s+from\b/i);
  assert.doesNotMatch(sql, /\btruncate\b/i);
  assert.doesNotMatch(sql, /get_contact_stats/i);
});

test('FastAPI compatibility migration adds owner, audit, and auth tables', () => {
  const sql = readMigration();

  assert.match(sql, /create table if not exists public\.users/i);
  assert.match(sql, /create table if not exists public\.auth_tokens/i);
  assert.match(sql, /add column if not exists owner_id uuid/i);
  assert.match(sql, /add column if not exists updated_at timestamptz/i);
  assert.match(sql, /add column if not exists created_by uuid/i);
  assert.match(sql, /add column if not exists updated_by uuid/i);
  assert.match(sql, /add column if not exists deleted_at timestamptz/i);
  assert.match(sql, /add column if not exists completed_at timestamptz/i);
  assert.match(sql, /add column if not exists first_name text/i);
  assert.match(sql, /add column if not exists preferred_contact_method text/i);
});

test('FastAPI compatibility migration blocks direct browser access without removing data', () => {
  const sql = readMigration();

  assert.match(sql, /alter table public\.students enable row level security/i);
  assert.match(sql, /drop policy if exists "demo read students"/i);
  assert.match(sql, /drop policy if exists "teachers read own students"/i);
  assert.doesNotMatch(sql, /create policy/i);
});
