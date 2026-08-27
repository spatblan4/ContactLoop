import assert from 'node:assert/strict';
import test from 'node:test';

const statsModuleUrl = new URL('../src/lib/dashboard-stats.js', import.meta.url);

test('total calls equals the sum of final outcomes and excludes pending calls', async () => {
  const { dashboardTotals = () => ({}) } = await import(statsModuleUrl).catch(() => ({}));
  const totals = dashboardTotals([
    { dateKey: 'today', result: 'Connected' },
    { dateKey: 'today', result: 'No Answer' },
    { dateKey: 'today', result: 'Busy' },
    { dateKey: 'today', result: 'Failed' },
    { dateKey: 'today', result: 'Initiated' },
    { dateKey: 'today', result: 'Ringing' },
    { dateKey: 'older', result: 'Connected' },
  ]);

  assert.deepEqual(totals, {
    calls: 4,
    connected: 1,
    noAnswer: 1,
    busy: 1,
    failed: 1,
    unsuccessful: 2,
  });
  assert.equal(totals.calls, totals.connected + totals.noAnswer + totals.busy + totals.failed);
});
