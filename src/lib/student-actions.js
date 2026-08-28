const STUDENT_DELETE_ORDER = Object.freeze([
  'teacher_notes',
  'ai_contact_briefs',
  'follow_ups',
  'contact_events',
  'guardians',
  'students',
]);

export function studentDeletionOrder() {
  return [...STUDENT_DELETE_ORDER];
}

export function studentDeletionRequests(studentId) {
  return [
    ...STUDENT_DELETE_ORDER.slice(0, -1).map(table => ({ table, column: 'student_id', value: studentId })),
    { table: 'students', column: 'id', value: studentId },
  ];
}
