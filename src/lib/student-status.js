const UNSUCCESSFUL_RESULTS = new Set(['No Answer', 'Busy', 'Failed']);

export function studentStatus(studentId, { events = [], followUps = [] } = {}) {
  const studentEvents = events
    .filter(event => event.studentId === studentId)
    .sort((a, b) => new Date(b.callTime).getTime() - new Date(a.callTime).getTime());
  const hasOpenFollowUp = followUps.some(followUp => followUp.studentId === studentId && (followUp.status || 'open') === 'open');
  if (!studentEvents.length) return 'not-contacted';
  if (hasOpenFollowUp || UNSUCCESSFUL_RESULTS.has(studentEvents[0].result)) return 'needs-follow-up';
  return 'on-track';
}

export function filterStudentsByStatus(students, status = 'all', context = {}) {
  if (status === 'all') return students;
  return students.filter(student => studentStatus(student.id, context) === status);
}
