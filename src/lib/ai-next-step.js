const DEFAULT_NEXT_STEP = 'No suggested next step recorded.';
const EMPTY_SUGGESTIONS = new Set(['', DEFAULT_NEXT_STEP.toLowerCase(), 'no suggestion.', 'none.']);

function followUpDate(value) {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? null : date;
}

export function groundBriefNextStep({ brief, studentId, followUps = [] }) {
  const nextBrief = { ...brief };
  const suggestion = String(nextBrief.suggested_next_step || '').trim();
  if (!EMPTY_SUGGESTIONS.has(suggestion.toLowerCase())) return nextBrief;

  const open = followUps
    .filter(followUp => followUp.studentId === studentId && followUp.status === 'open')
    .map(followUp => followUpDate(followUp.dueAt))
    .filter(Boolean)
    .sort((left, right) => left - right);

  if (open.length) {
    const dueDate = new Intl.DateTimeFormat('en-US', {
      weekday: 'long',
      month: 'long',
      day: 'numeric',
      year: 'numeric',
      timeZone: 'UTC',
    }).format(open[0]);
    nextBrief.suggested_next_step = `Follow up with the parent on ${dueDate}.`;
  } else {
    nextBrief.suggested_next_step = DEFAULT_NEXT_STEP;
  }

  return nextBrief;
}
