import { filterEventsByRange } from './date-filters.js';
import { discussedTopicsForEvent } from './call-topics.js';
import { effectiveOpenFollowUps } from './followup-items.js';

const FINAL_RESULTS = new Set(['Connected', 'No Answer', 'Busy', 'Failed']);
const UNSUCCESSFUL_RESULTS = new Set(['No Answer', 'Busy', 'Failed']);

function startOfDay(date) {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate());
}

function addDays(date, amount) {
  const next = new Date(date);
  next.setDate(next.getDate() + amount);
  return next;
}

function eventTime(event) {
  return new Date(event.callTime ?? event.call_time).getTime();
}

function newest(events) {
  return [...events].sort((left, right) => eventTime(right) - eventTime(left))[0];
}

function followUpStudentId(followUp) {
  return followUp.studentId ?? followUp.student_id;
}

function dueTodayOrOverdue(followUp, now) {
  const due = new Date(followUp.dueAt ?? followUp.due_at);
  return Number.isFinite(due.getTime()) && due.getTime() < addDays(startOfDay(now), 1).getTime();
}

function formatResult(result) {
  return result === 'No Answer' ? 'No answer' : result;
}

function topicCounts(events) {
  const counts = new Map();
  events.filter(event => FINAL_RESULTS.has(event.result)).forEach(event => {
    discussedTopicsForEvent(event).forEach(topic => counts.set(topic, (counts.get(topic) ?? 0) + 1));
  });
  return [...counts.entries()]
    .map(([label, count]) => ({ label, count }))
    .sort((left, right) => right.count - left.count || left.label.localeCompare(right.label))
    .slice(0, 3);
}

export function getDashboardInsights({ events = [], students = [], followUps = [], range = { preset: 'today' }, now = new Date() }) {
  const finalEvents = events.filter(event => FINAL_RESULTS.has(event.result));
  const rangeEvents = filterEventsByRange(finalEvents, range, now);
  const weekEvents = filterEventsByRange(finalEvents, { preset: 'this-week' }, now);
  const openFollowUps = effectiveOpenFollowUps({ followUps, events });
  const dueFollowUps = openFollowUps.filter(followUp => dueTodayOrOverdue(followUp, now));
  const todayEnd = addDays(startOfDay(now), 1).getTime();

  const needsFollowUp = students.map(student => {
    const studentEvents = weekEvents.filter(event => event.studentId === student.id || event.student_id === student.id);
    const latest = newest(studentEvents);
    const openFollowUp = openFollowUps
      .filter(followUp => followUpStudentId(followUp) === student.id)
      .sort((left, right) => new Date(left.dueAt ?? left.due_at).getTime() - new Date(right.dueAt ?? right.due_at).getTime())[0];
    const connectedThisWeek = studentEvents.some(event => event.result === 'Connected');

    if (connectedThisWeek) return null;
    if (openFollowUp && new Date(openFollowUp.dueAt ?? openFollowUp.due_at).getTime() <= todayEnd) {
      return { student, label: 'Follow-up due today', actionLabel: 'Call parent' };
    }
    if (latest && UNSUCCESSFUL_RESULTS.has(latest.result)) {
      return { student, label: `${formatResult(latest.result)} · Attempt #${latest.attemptNumber}`, actionLabel: 'Call again' };
    }
    if (studentEvents.length === 0) {
      return { student, label: 'No successful parent contact this week', actionLabel: 'Call parent' };
    }
    return { student, label: 'No successful parent contact this week', actionLabel: 'Call parent' };
  }).filter(Boolean);

  return {
    metrics: {
      callAttempts: rangeEvents.length,
      connected: rangeEvents.filter(event => event.result === 'Connected').length,
      unsuccessful: rangeEvents.filter(event => UNSUCCESSFUL_RESULTS.has(event.result)).length,
      followUpsDue: dueFollowUps.length,
    },
    needsFollowUp,
    weekBrief: {
      totalAttempts: weekEvents.length,
      successfulContacts: weekEvents.filter(event => event.result === 'Connected').length,
      studentsNeedingFollowUp: needsFollowUp.length,
      topTopics: topicCounts(weekEvents),
    },
  };
}
