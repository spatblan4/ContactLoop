const resultByStatus = {
  queued: 'Initiated',
  initiated: 'Initiated',
  ringing: 'Ringing',
  'in-progress': 'Connected',
  completed: 'Connected',
  'no-answer': 'No Answer',
  busy: 'Busy',
  failed: 'Failed',
  canceled: 'Failed',
};

function isoDate(value) {
  if (!value) return null;
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? null : date.toISOString();
}

export function contactEventUpdatesFromTwilioCall(call) {
  const status = String(call?.status || '').toLowerCase();
  const updates = {
    provider_call_id: String(call?.sid || ''),
    provider_status: status,
    result: resultByStatus[status] || 'Failed',
  };
  const duration = Number(call?.duration);
  const startedAt = isoDate(call?.start_time);
  const endedAt = isoDate(call?.end_time);

  if (Number.isFinite(duration) && duration >= 0 && call?.duration !== null && call?.duration !== undefined) {
    updates.duration_seconds = duration;
  }
  if (startedAt) updates.started_at = startedAt;
  if (endedAt) updates.ended_at = endedAt;
  return updates;
}

export function isTerminalTwilioStatus(status) {
  return ['completed', 'no-answer', 'busy', 'failed', 'canceled'].includes(String(status || '').toLowerCase());
}
