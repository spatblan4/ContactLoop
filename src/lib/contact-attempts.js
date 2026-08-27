const FINAL_RESULTS = new Set(['Connected', 'No Answer', 'Busy', 'Failed']);

function eventTime(event) {
  return new Date(event.callTime ?? event.call_time).getTime();
}

function sameContact(left, right) {
  return (left.studentId ?? left.student_id) === (right.studentId ?? right.student_id)
    && (left.guardianId ?? left.guardian_id) === (right.guardianId ?? right.guardian_id);
}

export function cycleAttemptNumber(events, targetEvent) {
  const relevant = events.filter(event => FINAL_RESULTS.has(event.result) && sameContact(event, targetEvent)).sort((left, right) => eventTime(left) - eventTime(right));
  let attempt = 0;
  for (const event of relevant) {
    attempt += 1;
    if (event.id === targetEvent.id) return attempt;
    if (event.result === 'Connected') attempt = 0;
  }
  return targetEvent.attemptNumber ?? 1;
}

export function nextAttemptNumber(events, studentId, guardianId) {
  const relevant = events.filter(event => FINAL_RESULTS.has(event.result)
    && (event.studentId ?? event.student_id) === studentId
    && (event.guardianId ?? event.guardian_id) === guardianId)
    .sort((left, right) => eventTime(left) - eventTime(right));
  let attempt = 0;
  for (const event of relevant) {
    attempt += 1;
    if (event.result === 'Connected') attempt = 0;
  }
  return attempt + 1;
}
