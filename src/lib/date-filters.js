function startOfDay(date) {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate());
}

function addDays(date, amount) {
  const next = new Date(date);
  next.setDate(next.getDate() + amount);
  return next;
}

function parseLocalDate(value) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value || '')) return null;
  const [year, month, day] = value.split('-').map(Number);
  const date = new Date(year, month - 1, day);
  return date.getFullYear() === year && date.getMonth() === month - 1 && date.getDate() === day ? date : null;
}

export function rangeBounds(range = { preset: 'today' }, now = new Date()) {
  const today = startOfDay(now);
  const preset = range.preset || 'today';
  if (preset === 'yesterday') return { start: addDays(today, -1), end: today };
  if (preset === 'this-week') {
    const mondayOffset = (today.getDay() + 6) % 7;
    const start = addDays(today, -mondayOffset);
    return { start, end: addDays(start, 7) };
  }
  if (preset === 'this-month') return { start: new Date(today.getFullYear(), today.getMonth(), 1), end: new Date(today.getFullYear(), today.getMonth() + 1, 1) };
  if (preset === 'this-year') return { start: new Date(today.getFullYear(), 0, 1), end: new Date(today.getFullYear() + 1, 0, 1) };
  if (preset === 'custom') {
    const start = parseLocalDate(range.from);
    const end = parseLocalDate(range.to);
    if (!start || !end || start > end) return null;
    return { start, end: addDays(end, 1) };
  }
  return { start: today, end: addDays(today, 1) };
}

export function filterEventsByRange(events, range, now = new Date()) {
  const bounds = rangeBounds(range, now);
  if (!bounds) return [];
  return events.filter(event => {
    const time = new Date(event.callTime ?? event.call_time).getTime();
    return Number.isFinite(time) && time >= bounds.start.getTime() && time < bounds.end.getTime();
  });
}

export function rangeLabel(range = { preset: 'today' }, now = new Date()) {
  const preset = range.preset || 'today';
  if (preset === 'yesterday') return 'Yesterday';
  if (preset === 'this-week') return 'This week';
  if (preset === 'this-month') return 'This month';
  if (preset === 'this-year') return 'This year';
  if (preset === 'custom') return range.from && range.to ? `${range.from} → ${range.to}` : 'Choose dates';
  return `Today · ${now.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}`;
}
