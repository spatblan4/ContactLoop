import test from 'node:test';
import assert from 'node:assert/strict';
import {
  CONTACTLOOP_TEMPLATE_HEADERS,
  buildImportPayload,
  groupImportRows,
  normalizeImportRows,
  parseCsvText,
  suggestColumnMapping,
  validateImportRows,
} from '../src/lib/import-students.js';

test('parses quoted CSV values and ignores blank rows', () => {
  const result = parseCsvText('Child,Parent 1,Relation,Cell Phone\n"Emma, Johnson",Sarah Johnson,Mom,"(415) 555-0188"\n,,,\n');
  assert.deepEqual(result.headers, ['Child', 'Parent 1', 'Relation', 'Cell Phone']);
  assert.deepEqual(result.rows, [{
    Child: 'Emma, Johnson',
    'Parent 1': 'Sarah Johnson',
    Relation: 'Mom',
    'Cell Phone': '(415) 555-0188',
  }]);
});

test('suggests only known aliases and flags unknown columns', () => {
  assert.deepEqual(suggestColumnMapping(['Child', 'Parent 1', 'Relation', 'Cell Phone', 'Mystery']), {
    Child: 'student_full_name',
    'Parent 1': 'guardian_name',
    Relation: 'relationship',
    'Cell Phone': 'phone',
    Mystery: null,
  });
});

test('normalizes full names and groups multiple guardians under one student', () => {
  const mapping = {
    Child: 'student_full_name',
    'Parent 1': 'guardian_name',
    Relation: 'relationship',
    'Cell Phone': 'phone',
  };
  const rows = normalizeImportRows([
    { Child: 'Emma Johnson', 'Parent 1': 'Sarah Johnson', Relation: 'Mom', 'Cell Phone': '415-555-0188' },
    { Child: ' Emma  Johnson ', 'Parent 1': 'David Johnson', Relation: 'Dad', 'Cell Phone': '415-555-0142' },
  ], mapping);
  const groups = groupImportRows(rows);
  assert.equal(groups.length, 1);
  assert.equal(groups[0].student.name, 'Emma Johnson');
  assert.equal(groups[0].guardians.length, 2);
});

test('marks missing relationship and duplicate students for review', () => {
  const rows = normalizeImportRows([
    { Student: 'Emma Johnson', Guardian: 'Sarah Johnson', Phone: '(415) 555-0188' },
    { Student: 'Lucas Smith', Guardian: 'David Smith', Relationship: 'Dad', Phone: '(415) 555-0142' },
  ], { Student: 'student_full_name', Guardian: 'guardian_name', Relationship: 'relationship', Phone: 'phone' });
  const result = validateImportRows(rows, [{ name: 'Lucas Smith', guardians: [{ phone: '(415) 555-0142' }] }]);
  assert.equal(result.stats.needsReview, 1);
  assert.equal(result.stats.duplicates, 1);
  assert.equal(result.rows[0].status, 'needs-review');
  assert.equal(result.rows[1].status, 'duplicate');
});

test('builds separate student and guardian payloads for duplicate student rows', () => {
  const rows = normalizeImportRows([
    { Student: 'Emma Johnson', Guardian: 'Sarah Johnson', Relationship: 'Mom', Phone: '415-555-0188' },
    { Student: 'Emma Johnson', Guardian: 'David Johnson', Relationship: 'Dad', Phone: '415-555-0142' },
  ], { Student: 'student_full_name', Guardian: 'guardian_name', Relationship: 'relationship', Phone: 'phone' });
  const payload = buildImportPayload(rows);
  assert.equal(payload.students.length, 1);
  assert.equal(payload.guardians.length, 2);
  assert.equal(payload.guardians[0].student_key, payload.guardians[1].student_key);
});

test('defines the six-column ContactLoop template', () => {
  assert.deepEqual(CONTACTLOOP_TEMPLATE_HEADERS, [
    'Student First Name',
    'Student Last Name',
    'Guardian Name',
    'Relationship',
    'Phone',
    'Email',
  ]);
});
