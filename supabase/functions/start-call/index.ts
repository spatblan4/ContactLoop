import { createClient } from 'https://esm.sh/@supabase/supabase-js@2';

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status, headers: { ...corsHeaders, 'Content-Type': 'application/json' } });

Deno.serve(async (request) => {
  if (request.method === 'OPTIONS') return new Response('ok', { headers: corsHeaders });
  try {
    const { studentId, plannedTopic = null } = await request.json();
    if (!studentId) return json({ error: 'studentId is required' }, 400);

    const supabaseUrl = Deno.env.get('SUPABASE_URL')!;
    const serviceKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;
    const accountSid = Deno.env.get('TWILIO_ACCOUNT_SID')!;
    const authToken = Deno.env.get('TWILIO_AUTH_TOKEN')!;
    const fromNumber = Deno.env.get('TWILIO_FROM_NUMBER')!;
    const admin = createClient(supabaseUrl, serviceKey);

    const { data: student, error: studentError } = await admin.from('students').select('id, name, guardians(id, phone)').eq('id', studentId).single();
    if (studentError || !student?.guardians?.[0]) return json({ error: 'Student or guardian phone not found.' }, 404);
    const guardian = student.guardians[0];
    const { data: history, error: historyError } = await admin.from('contact_events')
      .select('id, student_id, guardian_id, result, call_time, attempt_number')
      .eq('student_id', studentId)
      .eq('guardian_id', guardian.id)
      .order('call_time', { ascending: true });
    if (historyError) return json({ error: historyError.message }, 500);
    let currentAttempt = 0;
    for (const previous of history ?? []) {
      if (!['Connected', 'No Answer', 'Busy', 'Failed'].includes(previous.result)) continue;
      currentAttempt += 1;
      if (previous.result === 'Connected') currentAttempt = 0;
    }

    const { data: event, error: eventError } = await admin.from('contact_events').insert({
      student_id: student.id,
      guardian_id: guardian.id,
      call_time: new Date().toISOString(),
      result: 'Initiated',
      attempt_number: currentAttempt + 1,
      provider: 'twilio',
      provider_status: 'queued',
      planned_topic: typeof plannedTopic === 'string' && plannedTopic.trim() ? plannedTopic.trim() : null,
    }).select('id, attempt_number').single();
    if (eventError) return json({ error: eventError.message }, 500);

    const webhookUrl = `${supabaseUrl}/functions/v1/twilio-webhook?event_id=${event.id}`;
    const form = new URLSearchParams({
      To: guardian.phone,
      From: fromNumber,
      Url: 'https://webhooks.twilio.com/v1/Voice/Template/voice_text_to_speech',
      StatusCallback: webhookUrl,
    });
    const twilioResponse = await fetch(`https://api.twilio.com/2010-04-01/Accounts/${accountSid}/Calls.json`, {
      method: 'POST',
      headers: { Authorization: `Basic ${btoa(`${accountSid}:${authToken}`)}`, 'Content-Type': 'application/x-www-form-urlencoded' },
      body: form,
    });
    const twilioCall = await twilioResponse.json();
    if (!twilioResponse.ok) {
      const safeError = {
        status: twilioResponse.status,
        code: twilioCall.code ?? null,
        message: twilioCall.message || 'Twilio call failed.',
      };
      console.error('Twilio API rejected the call', safeError);
      await admin.from('contact_events').update({
        result: 'Failed',
        provider_status: `api-error-${twilioResponse.status}`,
        ended_at: new Date().toISOString(),
      }).eq('id', event.id);
      return json({ error: safeError.message, code: safeError.code }, 502);
    }

    await admin.from('contact_events').update({ provider_call_id: twilioCall.sid }).eq('id', event.id);
    return json({ eventId: event.id, providerCallId: twilioCall.sid, attemptNumber: event.attempt_number });
  } catch (error) {
    return json({ error: error instanceof Error ? error.message : 'Unable to start call.' }, 500);
  }
});
