export function newestContactEventsFirst(events) {
  return [...events].sort((left, right) => {
    const timeDifference = new Date(right.callTime).getTime() - new Date(left.callTime).getTime();
    return timeDifference || String(right.id).localeCompare(String(left.id));
  });
}

export function formatCallDuration(seconds) {
  if (!seconds) return null;
  if (seconds < 60) return `${seconds} sec`;
  const minutes = Math.floor(seconds / 60);
  return `${minutes}m ${String(seconds % 60).padStart(2, '0')}s`;
}
