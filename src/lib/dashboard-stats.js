const FINAL_RESULTS = new Set(['Connected', 'No Answer', 'Busy', 'Failed']);

export function dashboardTotals(events) {
  const finalToday = events.filter(event => event.dateKey === 'today' && FINAL_RESULTS.has(event.result));
  const connected = finalToday.filter(event => event.result === 'Connected').length;
  const noAnswer = finalToday.filter(event => event.result === 'No Answer').length;
  const busy = finalToday.filter(event => event.result === 'Busy').length;
  const failed = finalToday.filter(event => event.result === 'Failed').length;
  return {
    calls: connected + noAnswer + busy + failed,
    connected,
    noAnswer,
    busy,
    failed,
    unsuccessful: noAnswer + busy,
  };
}
