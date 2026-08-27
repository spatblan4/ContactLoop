import test from 'node:test';
import assert from 'node:assert/strict';
import { renderImportComplete, renderImportMapping, renderImportReview, renderImportUpload } from '../src/lib/import-students-view.js';

const baseState = { step: 'upload', fileName: '', headers: [], mapping: {}, rows: [], stats: null, error: null };

test('upload view includes the four-step import context and privacy-safe file controls', () => {
  const html = renderImportUpload(baseState);
  assert.match(html, /Import students/);
  assert.match(html, /Upload your existing student and guardian list/);
  assert.match(html, /\.csv, \.xlsx/);
  assert.match(html, /Download ContactLoop Template/);
  assert.match(html, /raw file stays in your browser/i);
});

test('mapping view renders source columns and target field dropdowns', () => {
  const html = renderImportMapping({ ...baseState, headers: ['Child', 'Parent 1'], mapping: { Child: 'student_full_name', 'Parent 1': 'guardian_name' } });
  assert.match(html, /Child/);
  assert.match(html, /Parent 1/);
  assert.match(html, /Student Full Name/);
  assert.match(html, /Guardian Name/);
  assert.match(html, /data-import-mapping/);
});

test('review view shows import counts, statuses, and duplicate actions', () => {
  const html = renderImportReview({ ...baseState, stats: { students: 1, guardians: 2, ready: 1, needsReview: 0, duplicates: 1 }, rows: [{ rowNumber: 2, student: { name: 'Emma Johnson' }, guardian: { name: 'Sarah Johnson', relationship: 'Mom', phone: '' }, status: 'duplicate', issues: ['Possible duplicate.'], action: 'import' }] });
  assert.match(html, /Ready to import/);
  assert.match(html, /1 student/);
  assert.match(html, /2 guardians/);
  assert.match(html, /Possible duplicate/);
  assert.match(html, /Skip/);
  assert.match(html, /Import as new/);
});

test('complete view shows imported counts and view students action', () => {
  const html = renderImportComplete({ students_imported: 2, guardians_imported: 3 });
  assert.match(html, /2 students imported/);
  assert.match(html, /3 guardian contacts imported/);
  assert.match(html, /Your student list is ready/);
  assert.match(html, /View Students/);
});
