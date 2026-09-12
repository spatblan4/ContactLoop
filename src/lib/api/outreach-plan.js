import { apiFetch, API_PREFIX } from './client.js';
import { getStoredToken } from './auth-token.js';

export function generateOutreachPlan(options) {
  return apiFetch(`${API_PREFIX}/ai/outreach-plan/generate`, { method: 'POST', ...options });
}

/**
 * Stream outreach plan generation over server-sent events.
 * `onProgress({event, data})` receives intermediate events (e.g. "message").
 * Resolves with the final plan payload; rejects on the "error" event.
 */
export async function generateOutreachPlanStream(onProgress) {
  const token = getStoredToken();
  const response = await fetch(`${API_PREFIX}/ai/outreach-plan/generate/stream`, {
    method: 'POST',
    headers: token ? { Authorization: `Bearer ${token}` } : undefined,
  });
  const contentType = response.headers.get('content-type') || '';
  if (!response.ok || !contentType.includes('text/event-stream')) {
    if (response.status === 503) throw new Error('Outreach Agent is temporarily unavailable. Try again shortly.');
    throw new Error(`Unable to stream outreach recommendations (${response.status}).`);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  let plan = null;
  let failure = null;

  const consumeBlock = (block) => {
    const lines = block.split('\n');
    const nameLine = lines.find(line => line.startsWith('event: '));
    const dataLine = lines.find(line => line.startsWith('data: '));
    if (!nameLine) return;
    const event = nameLine.slice('event: '.length).trim();
    const data = dataLine ? JSON.parse(dataLine.slice('data: '.length)) : {};
    if (event === 'plan') plan = data;
    else if (event === 'error') failure = new Error(data.detail || 'Outreach Agent is temporarily unavailable.');
    else if (onProgress) onProgress({ event, data });
  };

  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    let boundary;
    while ((boundary = buffer.indexOf('\n\n')) !== -1) {
      const block = buffer.slice(0, boundary);
      buffer = buffer.slice(boundary + 2);
      consumeBlock(block);
    }
  }
  if (buffer.trim()) consumeBlock(buffer);

  if (failure) throw failure;
  if (!plan) throw new Error('The Outreach Agent returned no plan.');
  return plan;
}
