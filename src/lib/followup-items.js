const UNSUCCESSFUL_RESULTS = new Set(['No Answer', 'Busy', 'Failed']);

function startOfDay(date) {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate());
}

function followUpStudentId(followUp) {
  return followUp.studentId ?? followUp.student_id;
}

function followUpGuardianId(followUp) {
  return followUp.guardianId ?? followUp.guardian_id ?? null;
}

function eventTime(event) {
  return new Date(event.callTime ?? event.call_time).getTime();
}

function sortNewest(events) {
  return [...events].sort((left, right) => eventTime(right) - eventTime(left));
}

function formatDateTime(value) {
  return new Intl.DateTimeFormat('en-US', {
    month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit',
  }).format(new Date(value)).replace(',', ' ·');
}

function sameTask(left, right) {
  return followUpStudentId(left) === followUpStudentId(right)
    && (!followUpGuardianId(left) || !followUpGuardianId(right) || followUpGuardianId(left) === followUpGuardianId(right));
}

export function followUpGroup(value, now = new Date()) {
  const due = startOfDay(new Date(value));
  const today = startOfDay(now);
  const dayDifference = Math.round((due.getTime() - today.getTime()) / 86400000);
  if (dayDifference <= 0) return 'TODAY';
  if (dayDifference === 1) return 'TOMORROW';
  return 'UPCOMING';
}

export function buildFollowUpItems({ followUps = [], events = [], students = [], now = new Date() }) {
  const openFollowUps = followUps.filter(followUp => (followUp.status ?? 'open') === 'open');
  const uniqueFollowUps = openFollowUps.filter((followUp, index, all) => all.findIndex(candidate => sameTask(candidate, followUp)) === index);

  return uniqueFollowUps.map(followUp => {
    const studentId = followUpStudentId(followUp);
    const guardianId = followUpGuardianId(followUp);
    const student = students.find(candidate => candidate.id === studentId);
    const studentEvents = sortNewest(events.filter(event => {
      const sameStudent = (event.studentId ?? event.student_id) === studentId;
      const sameGuardian = !guardianId || !event.guardianId || event.guardianId === guardianId || event.guardian_id === guardianId;
      return sameStudent && sameGuardian;
    }));
    const latest = studentEvents[0];
    const unsuccessfulAttempts = studentEvents.filter(event => UNSUCCESSFUL_RESULTS.has(event.result)).length;
    const dueAt = followUp.dueAt ?? followUp.due_at;
    const resultLabel = latest?.result === 'No Answer' ? 'No answer' : latest?.result ?? 'Follow-up';

    return {
      id: followUp.id,
      student,
      dueAt,
      group: followUpGroup(dueAt, now),
      summary: unsuccessfulAttempts > 1 ? `${unsuccessfulAttempts} unsuccessful attempts` : `${resultLabel} · Attempt #${latest?.attemptNumber ?? '—'}`,
      lastResult: latest?.result ?? null,
      attemptNumber: latest?.attemptNumber ?? null,
      lastCallTime: latest?.callTime ?? latest?.call_time ?? null,
      lastContact: latest ? formatDateTime(latest.callTime ?? latest.call_time) : 'No contact recorded',
      nextFollowUp: formatDateTime(dueAt),
    };
  }).filter(item => item.student);
}
