import { supabase } from './supabase.js';

export const TELEPHONY_PROVIDER = import.meta.env.VITE_TELEPHONY_PROVIDER || 'mock';

export class MockTelephonyProvider {
  async startCall(studentId, { plannedTopic = null } = {}) {
    return { provider: 'mock', studentId, mode: 'mock' };
  }

  async syncCallStatus() {
    return { synced: [] };
  }
}

export class TwilioTelephonyProvider {
  async startCall(studentId) {
    if (!supabase) throw new Error('Supabase is not configured.');
    const { data, error } = await supabase.functions.invoke('start-call', { body: { studentId, plannedTopic } });
    if (error) {
      let message = error.message;
      try {
        const payload = await error.context?.json();
        message = payload?.error || message;
      } catch {
        // Keep the SDK's fallback message when the response has no JSON body.
      }
      throw new Error(message);
    }
    return { ...data, provider: 'twilio', mode: 'real' };
  }

  async syncCallStatus(eventId = null) {
    if (!supabase) throw new Error('Supabase is not configured.');
    const { data, error } = await supabase.functions.invoke('sync-call-status', {
      body: eventId ? { eventId } : {},
    });
    if (error) {
      let message = error.message;
      try {
        const payload = await error.context?.json();
        message = payload?.error || message;
      } catch {
        // Keep the SDK fallback when the response has no JSON body.
      }
      throw new Error(message);
    }
    return data;
  }
}

export function getTelephonyProvider() {
  return TELEPHONY_PROVIDER === 'twilio' ? new TwilioTelephonyProvider() : new MockTelephonyProvider();
}
