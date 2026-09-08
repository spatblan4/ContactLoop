import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const appSource = fs.readFileSync(path.join(here, '../src/app.js'), 'utf8');
const htmlSource = fs.readFileSync(path.join(here, '../index.html'), 'utf8');
const styles = fs.readFileSync(path.join(here, '../src/styles.css'), 'utf8');

test('student mutations give a visible success confirmation', () => {
  assert.match(htmlSource, /id="toast-root"/);
  assert.match(appSource, /showToast\('Student added'\)/);
  assert.match(appSource, /showToast\('Student updated'\)/);
  assert.match(appSource, /showToast\('Student deleted'\)/);
});

test('manual call outcome flow never invents a call duration', () => {
  assert.match(appSource, /\['Connected','Log a completed conversation'\]/);
  assert.match(appSource, /durationSeconds:null/);
  assert.doesNotMatch(appSource, /durationSeconds:m\.result==='Connected'\?463:null/);
  assert.doesNotMatch(appSource, /outcomeCopyObserver/);
  assert.match(styles, /✓ Connected · Logged manually/);
});
