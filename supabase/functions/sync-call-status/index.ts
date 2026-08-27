import { createClient } from 'https://esm.sh/@supabase/supabase-js@2';
import { contactEventUpdatesFromTwilioCall, isTerminalTwilioStatus } from './twilio-call-status.js';

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};
const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), {
  status,
  headers: { ...corsHeaders, 'Content-Type': 'application/json' },
});

Deno.serve(async (request) => {
  if (request.method === 'OPTIONS') return new Response('ok', { headers: corsHeaders });
  try {
    const body = await request.json().catch(() => ({}));
    const eventId = typeof body.eventId === 'string' ? body.eventId : null;
    const supabaseUrl = Deno.env.get('SUPABASE_URL')!;
    const accountSid = Deno.env.get('TWILIO_ACCOUNT_SID')!;
    const authToken = Deno.env.get('TWILIO_AUTH_TOKEN')!;
    const admin = createClient(supabaseUrl, Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!);

    let query = admin
      .from('contact_events')
      .select('id, provider_call_id')
      .eq('provider', 'twilio')
      .not('provider_call_id', 'is', null)
      .is('ended_at', null)
      .order('call_time', { ascending: false })
      .limit(eventId ? 1 : 25);
    if (eventId) query = query.eq('id', eventId);
    const { data: events, error: eventsError } = await query;
    if (eventsError) return json({ error: eventsError.message }, 500);
    if (eventId && !events?.length) return json({ error: 'Pending call was not found.' }, 404);

    const synced = [];
    for (const event of events ?? []) {
      const callResponse = await fetch(
        `https://api.twilio.com/2010-04-01/Accounts/${accountSid}/Calls/${encodeURIComponent(event.provider_call_id)}.json`,
        { headers: { Authorization: `Basic ${btoa(`${accountSid}:${authToken}`)}` } },
      );
      const call = await callResponse.json();
      if (!callResponse.ok) {
        console.error('Unable to synchronize Twilio call', {
          eventId: event.id,
          status: callResponse.status,
          code: call.code ?? null,
        });
        synced.push({ eventId: event.id, error: call.message || 'Twilio status lookup failed.' });
        continue;
      }

      const updates = contactEventUpdatesFromTwilioCall(call);
      const { error: updateError } = await admin.from('contact_events').update(updates).eq('id', event.id);
      if (updateError) {
        synced.push({ eventId: event.id, error: updateError.message });
        continue;
      }
      synced.push({
        eventId: event.id,
        status: updates.provider_status,
        result: updates.result,
        durationSeconds: updates.duration_seconds ?? null,
        terminal: isTerminalTwilioStatus(updates.provider_status),
      });
    }
    return json({ synced });
  } catch (error) {
    return json({ error: error instanceof Error ? error.message : 'Unable to synchronize call status.' }, 500);
  }
});
