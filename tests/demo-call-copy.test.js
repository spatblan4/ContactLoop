import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const appSource = fs.readFileSync(path.join(here, '../src/app.js'), 'utf8');
const styles = fs.readFileSync(path.join(here, '../src/styles.css'), 'utf8');
const schema = fs.readFileSync(path.join(here, '../supabase/schema.sql'), 'utf8');

test('mock call workflow is labeled as a demo and never claims a fabricated duration', () => {
  assert.match(appSource, /Demo simulation/);
  assert.doesNotMatch(`${appSource}\n${styles}`, /7m 43s/);
  assert.doesNotMatch(appSource, /durationSeconds:m\.result==='Connected'\?463:null/);
  assert.doesNotMatch(schema, /\b463, 'Connected'/);
});
