const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
};

const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), {
  status,
  headers: { ...corsHeaders, 'Content-Type': 'application/json' },
});

Deno.serve(async request => {
  if (request.method === 'OPTIONS') return new Response('ok', { headers: corsHeaders });
  if (request.method !== 'POST') return json({ error: 'Method not allowed.' }, 405);

  try {
    const body = await request.json();
    const endpoint = Deno.env.get('CONTACT_BRIEF_ENDPOINT')
      || 'https://brzo25x3dq5gk45z3a447w2gam0nhkfx.lambda-url.us-east-2.on.aws';
    const response = await fetch(`${endpoint.replace(/\/$/, '')}/contact-brief`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    const text = await response.text();
    let payload: unknown;
    try {
      payload = JSON.parse(text);
    } catch {
      payload = { error: text || 'Contact Brief provider returned an invalid response.' };
    }
    return json(payload, response.status);
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unable to reach Contact Brief provider.';
    console.error('contact-brief-proxy failed:', message);
    return json({ error: message }, 502);
  }
});
