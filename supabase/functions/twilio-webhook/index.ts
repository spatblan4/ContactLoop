import { createClient } from 'https://esm.sh/@supabase/supabase-js@2';
import { validateTwilioSignature } from './twilio-signature.js';

const corsHeaders = { 'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type' };

Deno.serve(async (request) => {
  if (request.method === 'OPTIONS') return new Response('ok', { headers: corsHeaders });
  try {
    const url = new URL(request.url);
    const eventId = url.searchParams.get('event_id');
    const form = await request.formData();
    const signatureIsValid = await validateTwilioSignature({
      url: request.url,
      formData: form,
      signature: request.headers.get('X-Twilio-Signature'),
      authToken: Deno.env.get('TWILIO_AUTH_TOKEN') || '',
    });
    if (!signatureIsValid) return new Response('Invalid Twilio signature', { status: 403, headers: corsHeaders });
    const callStatus = String(form.get('CallStatus') || '');
    const callDuration = Number(form.get('CallDuration') || 0) || null;
    const callSid = String(form.get('CallSid') || '');
    if (!eventId) return new Response('Missing event_id', { status: 400 });

    const statusMap: Record<string, string> = {
      initiated: 'Initiated', ringing: 'Ringing', answered: 'Connected', completed: 'Connected',
      'no-answer': 'No Answer', busy: 'Busy', failed: 'Failed', canceled: 'Failed',
    };
    const result = statusMap[callStatus] || 'Failed';
    const admin = createClient(Deno.env.get('SUPABASE_URL')!, Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!);
    const updates: Record<string, unknown> = {
      provider_status: callStatus,
      provider_call_id: callSid || undefined,
      result,
    };
    if (callStatus === 'answered') updates.started_at = new Date().toISOString();
    if (['completed', 'no-answer', 'busy', 'failed', 'canceled'].includes(callStatus)) {
      updates.ended_at = new Date().toISOString();
      if (callDuration) updates.duration_seconds = callDuration;
    }
    await admin.from('contact_events').update(updates).eq('id', eventId);
    return new Response('<Response></Response>', { headers: { ...corsHeaders, 'Content-Type': 'text/xml' } });
  } catch (error) {
    return new Response(error instanceof Error ? error.message : 'Webhook error', { status: 500, headers: corsHeaders });
  }
});
