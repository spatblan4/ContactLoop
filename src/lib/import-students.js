import * as XLSX from 'xlsx';

export const CONTACTLOOP_TEMPLATE_HEADERS = [
  'Student First Name',
  'Student Last Name',
  'Guardian Name',
  'Relationship',
  'Phone',
  'Email',
];

export const IMPORT_TARGET_FIELDS = [
  'student_first_name',
  'student_last_name',
  'student_full_name',
  'guardian_name',
  'relationship',
  'phone',
  'email',
];

const aliases = new Map([
  ['student first name', 'student_first_name'],
  ['first name', 'student_first_name'],
  ['student last name', 'student_last_name'],
  ['last name', 'student_last_name'],
  ['student full name', 'student_full_name'],
  ['student name', 'student_full_name'],
  ['child', 'student_full_name'],
  ['child name', 'student_full_name'],
  ['guardian name', 'guardian_name'],
  ['parent', 'guardian_name'],
  ['parent 1', 'guardian_name'],
  ['primary contact', 'guardian_name'],
  ['relationship', 'relationship'],
  ['relation', 'relationship'],
  ['phone', 'phone'],
  ['phone number', 'phone'],
  ['cell phone', 'phone'],
  ['cell #', 'phone'],
  ['mobile', 'phone'],
  ['email', 'email'],
  ['email address', 'email'],
]);

const cleanHeader = value => String(value ?? '').trim();
const canonicalHeader = value => cleanHeader(value).toLowerCase().replace(/[_-]+/g, ' ').replace(/\s+/g, ' ');
const cleanValue = value => String(value ?? '').trim();

export function normalizeName(value) {
  return cleanValue(value).toLowerCase().replace(/[^\p{L}\p{N}]+/gu, ' ').trim().replace(/\s+/g, ' ');
}

export function normalizePhone(value) {
  return cleanValue(value).replace(/\D/g, '');
}

function parseCsvLine(line) {
  const values = [];
  let value = '';
  let quoted = false;
  for (let index = 0; index < line.length; index += 1) {
    const char = line[index];
    if (char === '"' && quoted && line[index + 1] === '"') {
      value += '"';
      index += 1;
    } else if (char === '"') {
      quoted = !quoted;
    } else if (char === ',' && !quoted) {
      values.push(value);
      value = '';
    } else {
      value += char;
    }
  }
  values.push(value);
  return values;
}

function parseCsvLines(text) {
  const lines = [];
  let line = '';
  let quoted = false;
  for (let index = 0; index < String(text ?? '').length; index += 1) {
    const char = String(text ?? '')[index];
    if (char === '"') quoted = !quoted;
    if ((char === '\n' || char === '\r') && !quoted) {
      if (char === '\r' && String(text ?? '')[index + 1] === '\n') index += 1;
      lines.push(line);
      line = '';
    } else {
      line += char;
    }
  }
  if (line || lines.length === 0) lines.push(line);
  return lines;
}

export function parseCsvText(text) {
  const lines = parseCsvLines(text).filter(line => line.trim());
  if (!lines.length) return { headers: [], rows: [] };
  const headers = parseCsvLine(lines[0]).map(cleanHeader);
  const rows = lines.slice(1).map(line => parseCsvLine(line)).map(values => Object.fromEntries(
    headers.map((header, index) => [header, cleanValue(values[index])]),
  )).filter(row => Object.values(row).some(Boolean));
  return { headers, rows };
}

export function parseWorkbook(buffer) {
  const workbook = XLSX.read(buffer, { type: 'array', cellDates: false });
  const firstSheet = workbook.Sheets[workbook.SheetNames[0]];
  if (!firstSheet) return { headers: [], rows: [] };
  const rows = XLSX.utils.sheet_to_json(firstSheet, { defval: '', raw: false });
  const headers = rows.length ? Object.keys(rows[0]).map(cleanHeader) : [];
  return {
    headers,
    rows: rows.map(row => Object.fromEntries(headers.map(header => [header, cleanValue(row[header])]))),
  };
}

export function suggestColumnMapping(headers) {
  const used = new Set();
  return Object.fromEntries(headers.map(header => {
    const candidate = aliases.get(canonicalHeader(header)) ?? null;
    const mapping = candidate && !used.has(candidate) ? candidate : null;
    if (mapping) used.add(mapping);
    return [header, mapping];
  }));
}

function valueForTarget(row, mapping, target) {
  const source = Object.entries(mapping).find(([, mappedTarget]) => mappedTarget === target)?.[0];
  return cleanValue(source ? row[source] : '');
}

function splitFullName(fullName) {
  const parts = cleanValue(fullName).split(/\s+/).filter(Boolean);
  if (parts.length < 2) return { firstName: parts[0] ?? '', lastName: '' };
  return { firstName: parts.slice(0, -1).join(' '), lastName: parts.at(-1) };
}

export function normalizeImportRows(rows, mapping) {
  return rows.map((row, index) => {
    const fullName = valueForTarget(row, mapping, 'student_full_name');
    const splitName = splitFullName(fullName);
    const firstName = valueForTarget(row, mapping, 'student_first_name') || splitName.firstName;
    const lastName = valueForTarget(row, mapping, 'student_last_name') || splitName.lastName;
    const studentName = [firstName, lastName].filter(Boolean).join(' ') || fullName;
    const guardianName = valueForTarget(row, mapping, 'guardian_name');
    return {
      rowNumber: index + 2,
      student: { firstName, lastName, name: studentName },
      guardian: {
        name: guardianName,
        relationship: valueForTarget(row, mapping, 'relationship'),
        phone: valueForTarget(row, mapping, 'phone'),
        email: valueForTarget(row, mapping, 'email'),
      },
      studentKey: normalizeName(studentName),
      guardianPhoneKey: normalizePhone(valueForTarget(row, mapping, 'phone')),
      status: 'ready',
      issues: [],
      action: 'import',
    };
  });
}

export function groupImportRows(rows) {
  const groups = new Map();
  rows.forEach(row => {
    if (!groups.has(row.studentKey)) groups.set(row.studentKey, { student: row.student, studentKey: row.studentKey, guardians: [] });
    groups.get(row.studentKey).guardians.push(row.guardian);
  });
  return [...groups.values()];
}

export function validateImportRows(rows, existingStudents = []) {
  const existingNames = new Set(existingStudents.map(student => normalizeName(student.name || [student.first_name, student.last_name].filter(Boolean).join(' '))));
  const existingPhones = new Set(existingStudents.flatMap(student => (student.guardians ?? []).map(guardian => normalizePhone(guardian.phone)).filter(Boolean)));
  const seenRows = new Set();
  const validatedRows = rows.map(row => {
    const issues = [];
    if (!row.studentKey) issues.push('Student name is required.');
    if (!normalizeName(row.guardian.name)) issues.push('Guardian name is required.');
    if (!cleanValue(row.guardian.relationship)) issues.push('Relationship is required.');
    const rowKey = `${row.studentKey}|${normalizeName(row.guardian.name)}|${row.guardianPhoneKey}`;
    const duplicate = existingNames.has(row.studentKey)
      || (row.guardianPhoneKey && existingPhones.has(row.guardianPhoneKey))
      || seenRows.has(rowKey);
    if (duplicate) issues.push('Possible duplicate.');
    seenRows.add(rowKey);
    return { ...row, status: issues.includes('Possible duplicate.') ? 'duplicate' : issues.length ? 'needs-review' : 'ready', issues };
  });
  return {
    rows: validatedRows,
    stats: {
      students: new Set(validatedRows.map(row => row.studentKey).filter(Boolean)).size,
      guardians: validatedRows.filter(row => row.guardian.name).length,
      ready: validatedRows.filter(row => row.status === 'ready').length,
      needsReview: validatedRows.filter(row => row.status === 'needs-review').length,
      duplicates: validatedRows.filter(row => row.status === 'duplicate').length,
    },
  };
}

export function buildImportPayload(rows) {
  const groups = groupImportRows(rows);
  return {
    students: groups.map(group => ({
      student_key: group.studentKey,
      first_name: group.student.firstName,
      last_name: group.student.lastName,
      name: group.student.name,
    })),
    guardians: groups.flatMap(group => group.guardians.map(guardian => ({
      student_key: group.studentKey,
      name: guardian.name,
      relationship: guardian.relationship,
      phone: guardian.phone,
      email: guardian.email,
    }))),
  };
}

export function downloadContactLoopTemplate() {
  const csv = `${CONTACTLOOP_TEMPLATE_HEADERS.join(',')}\n`;
  const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8' }));
  const link = document.createElement('a');
  link.href = url;
  link.download = 'contactloop-student-template.csv';
  link.click();
  URL.revokeObjectURL(url);
}
