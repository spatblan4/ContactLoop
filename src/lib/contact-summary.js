const FINAL_RESULTS = new Set(['Connected', 'No Answer', 'Busy', 'Failed']);

export function buildContactSummaryStats({ studentId, events = [], followUps = [] }) {
  const studentEvents = events.filter(event => event.studentId === studentId && FINAL_RESULTS.has(event.result));
  const connected = studentEvents.filter(event => event.result === 'Connected').length;
  const openFollowUps = followUps.filter(followUp => {
    const followUpStudentId = followUp.studentId ?? followUp.student_id;
    return followUpStudentId === studentId && (followUp.status ?? 'open') === 'open';
  }).length;

  return {
    attempts: studentEvents.length,
    connected,
    unsuccessful: studentEvents.length - connected,
    openFollowUps,
  };
}
