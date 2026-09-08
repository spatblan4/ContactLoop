import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const appSource = fs.readFileSync(path.join(here, '../src/app.js'), 'utf8');

test('Demo outreach copy is initialized before application state uses it', () => {
  const demoCopy = appSource.indexOf('const DEMO_OUTREACH_COPY =');
  const applicationState = appSource.indexOf('let state = {');

  assert.ok(demoCopy >= 0, 'Demo outreach copy should be declared.');
  assert.ok(applicationState >= 0, 'Application state should be declared.');
  assert.ok(demoCopy < applicationState, 'Demo outreach copy must be declared before application state.');
});
