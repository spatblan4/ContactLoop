import { effectiveOpenFollowUps } from './followup-items.js';

const FINAL_RESULTS = new Set(['Connected', 'No Answer', 'Busy', 'Failed']);

export function buildContactSummaryStats({ studentId, events = [], followUps = [] }) {
  const studentEvents = events.filter(event => event.studentId === studentId && FINAL_RESULTS.has(event.result));
  const connected = studentEvents.filter(event => event.result === 'Connected').length;
  const openFollowUps = effectiveOpenFollowUps({ followUps, events })
    .filter(followUp => (followUp.studentId ?? followUp.student_id) === studentId)
    .length;

  return {
    attempts: studentEvents.length,
    connected,
    unsuccessful: studentEvents.length - connected,
    openFollowUps,
  };
}
