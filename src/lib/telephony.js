import { apiFetch, API_PREFIX } from './api/client.js';

export const TELEPHONY_PROVIDER = import.meta.env?.VITE_TELEPHONY_PROVIDER || 'mock';

export class MockTelephonyProvider {
  async startCall(studentId, { plannedTopic = null } = {}) {
    return { provider: 'mock', studentId, mode: 'mock' };
  }

  async syncCallStatus() {
    return { synced: [] };
  }
}

export class TwilioTelephonyProvider {
  async startCall(studentId, { plannedTopic = null } = {}) {
    return apiFetch(`${API_PREFIX}/telephony/calls`, {
      method: 'POST',
      body: { student_id: studentId, planned_topic: plannedTopic },
    });
  }

  async syncCallStatus(eventId = null) {
    if (!eventId) return { synced: [] };
    return apiFetch(`${API_PREFIX}/telephony/call-status-sync`, {
      method: 'POST',
      body: { event_id: eventId },
    });
  }
}

export function getTelephonyProvider() {
  return TELEPHONY_PROVIDER === 'twilio' ? new TwilioTelephonyProvider() : new MockTelephonyProvider();
}
