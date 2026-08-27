# ContactLoop AI provider layer

This directory contains an independent AWS provider. It does not replace the
Twilio provider, Supabase client, or call-status functions.

The AWS service uses:

- Strands Agents SDK (`strands-agents`)
- Amazon Bedrock through `BedrockModel`
- Read-only Supabase REST access with the service-role key kept server-side
- `get_contact_stats` Supabase RPC for all authoritative numbers

The agent tools are intentionally narrow:

- `get_contact_stats`
- `get_teacher_notes_and_topics`
- `get_open_follow_ups`

The returned payload has `review_status: "pending"`. The browser should not put
the narrative into a final printable brief until a teacher approves it.

## Run/deploy shape

Package this folder as an AWS Lambda or deploy it as a small AWS service. Set:

```text
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=server-only-secret
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=us.anthropic.claude-sonnet-4-6
```

Run `supabase/patch-ai-contact-brief.sql` once before calling the service. The
frontend provider adapter is `src/lib/ai-provider.js` and expects:

```text
POST {endpoint}/contact-brief
{
  "student_id": "...",
  "date_from": "2026-08-01T00:00:00Z",
  "date_to": "2026-09-01T00:00:00Z",
  "include_notes": true
}
```

The service must never expose the Supabase service-role key to the browser.
There is no voice-to-text, recording, or transcription code in this provider.
