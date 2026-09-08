# ContactLoop Contact Brief Lambda

This directory contains the provider code used by the existing Contact Brief Lambda.
It is separate from the Outreach Agent, which runs locally inside FastAPI at
`backend/app/services/outreach_plan_agent.py`.

## Request path

```text
Browser -> authenticated FastAPI -> existing Contact Brief Lambda
                                -> Strands Agent -> Amazon Bedrock
```

FastAPI verifies that the selected student belongs to the signed-in teacher before
calling the Lambda. The browser never receives the Lambda endpoint, AWS credentials,
or a Supabase service-role key.

## Provider behavior

The existing AWS path uses:

- Strands Agents SDK (`strands-agents`)
- Amazon Bedrock through `BedrockModel`
- Read-only Supabase REST access with the service-role key kept server-side
- `get_contact_stats` Supabase RPC for all authoritative numbers

The agent tools are intentionally narrow:

- `get_contact_stats`
- `get_teacher_notes_and_topics`
- `get_open_follow_ups`

The returned payload has `review_status: "pending"`. FastAPI returns it to the
browser, where it is saved as a draft for teacher editing and approval.

The Agent does not place calls, send messages, or create follow-ups.

## Existing deployment configuration

The ContactLoop Demo keeps its already-deployed Lambda in `us-east-2`. Do not create
or replace a Lambda merely to run the local Outreach Agent. The deployed Lambda owns
these server-side environment variables:

```text
SUPABASE_URL=<server-only-project-url>
SUPABASE_SERVICE_ROLE_KEY=<server-only-key>
AWS_REGION=us-east-2
BEDROCK_MODEL_ID=<configured-bedrock-model-id>
```

Never commit populated values. This README documents the existing path; it is not an
instruction to deploy, overwrite, or subscribe to a new model.

## API contract

FastAPI calls the Lambda's `/contact-brief` route with:

```text
POST {endpoint}/contact-brief
{
  "student_id": "...",
  "date_from": "2026-08-01T00:00:00Z",
  "date_to": "2026-09-01T00:00:00Z",
  "include_notes": true
}
```

There is no Twilio calling, voice recording, transcription, or Outreach Plan code in
this directory.
