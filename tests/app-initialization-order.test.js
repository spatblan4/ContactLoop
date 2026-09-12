import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const appSource = fs.readFileSync(path.join(here, '../src/app.js'), 'utf8');

test('Demo outreach plan is imported before application state uses it', () => {
  const demoImport = appSource.indexOf("from './lib/demo-outreach-plan.js'");
  const applicationState = appSource.indexOf('let state = {');

  assert.ok(demoImport >= 0, 'Demo outreach plan module should be imported.');
  assert.ok(applicationState >= 0, 'Application state should be declared.');
  assert.ok(demoImport < applicationState, 'Demo outreach plan must be imported before application state.');
});
