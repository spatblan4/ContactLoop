# ContactLoop Builder Articles Evidence Matrix

This file is the factual source of truth for the three AWS Builder drafts. It is not publication copy.

## Approved terminology

- Product: `ContactLoop`
- Generated artifact: `Contact Brief`
- Draft state shown to the teacher: `Needs Teacher Review`
- Approved state shown to the teacher: `Teacher Approved`
- Intent selected before outreach: `planned topic`
- Topics confirmed after a connected call: `discussed topics`
- Unresolved next action: `open follow-up`

## Claims

| Claim | Evidence | Allowed wording | Prohibited wording | Articles |
| --- | --- | --- | --- | --- |
| ContactLoop initiates real calls through Twilio. | `src/lib/telephony.js`; `supabase/functions/start-call/index.ts`; user confirmed the live end-to-end flow on 2026-09-06. | “ContactLoop can place a real call through Twilio.” | “ContactLoop works with every carrier and phone configuration.” | 1, 2 |
| Call results return to ContactLoop and persist. | `src/lib/telephony.js`; `supabase/functions/sync-call-status/index.ts`; `supabase/functions/twilio-webhook/index.ts`; user confirmation. | “The result of the call returns to ContactLoop and becomes part of the contact history.” | “Call-status delivery can never fail.” | 1, 2 |
| Contact events are associated with a student and guardian. | `supabase/schema.sql`; `src/app.js`; `supabase/functions/start-call/index.ts`. | “The event is connected to the relevant student and guardian.” | “The system always identifies a caller automatically.” | 1, 2 |
| A planned topic is not treated as a discussed topic after an unsuccessful call. | `tests/contact-event-order.test.js`; `src/app.js`; `ai/contact_brief/provider.py`. | “A planned topic records intent; discussed topics are confirmed only after a connected call.” | “The AI knows what was discussed from the phone call.” | 2, 3 |
| Open follow-ups remain visible until resolved by the workflow. | `src/lib/followup-items.js`; `tests/followup-items.test.js`. | “Unresolved outreach remains visible as an open follow-up.” | “No follow-up can ever be missed.” | 1, 2, 3 |
| The AWS provider uses Strands Agents SDK. | `ai/contact_brief/provider.py`; `ai/contact_brief/tools.py`; `ai/requirements.txt`. | “A Strands Agent orchestrates narrow tools to prepare the brief.” | “Strands independently controls the whole application.” | 2 |
| Amazon Bedrock provides the model used by the Strands Agent. | `ai/contact_brief/provider.py`; `ai/README.md`. | “The Strands Agent uses a model through Amazon Bedrock.” | “Amazon Bedrock verifies every statement.” | 2 |
| The agent has three narrow information-retrieval tools. | `ai/contact_brief/tools.py`. | Name their responsibilities: authoritative contact statistics; teacher notes and discussed topics; open follow-ups. | Publish full prompts, credentials, or sensitive payloads. | 2 |
| Numerical contact statistics come from Supabase rather than model calculation. | `ai/contact_brief/tools.py`; `ai/contact_brief/provider.py`; `ai/contact_brief/supabase_reader.py`. | “Authoritative counts come from a Supabase RPC and are attached separately.” | “The model calculates verified statistics.” | 2, 3 |
| Supabase stores persistent communication data. | `supabase/schema.sql`; `ai/contact_brief/supabase_reader.py`; `src/lib/supabase.js`. | “Supabase is the persistent source for contact events and workflow data.” | “Supabase alone guarantees accuracy or compliance.” | 2, 3 |
| A generated Contact Brief begins pending teacher review. | `ai/contact_brief/provider.py`; `ai/README.md`; `src/app.js`. | “Every generated brief starts as Needs Teacher Review.” | “The AI creates a final official record automatically.” | 1, 2, 3 |
| Teachers can edit and approve generated material. | `src/lib/ai-summary-editor.js`; `src/app.js`; `tests/ai-summary-editor.test.js`. | “The teacher can correct, add context to, and approve the brief.” | “Teacher approval proves that every underlying fact is objectively true.” | 2, 3 |
| ContactLoop does not record parent calls or automatically transcribe family conversations. | `ai/README.md`; `docs/ContactLoop Devpost Video Script — Condensed.md`; current implementation boundaries. | “ContactLoop does not record the parent call or automatically transcribe the family conversation.” | Any claim that the system listens to or analyzes call audio. | 1, 3 |
| Voice notes are a separate teacher-controlled input. | `src/lib/voice-note.js`; `src/lib/demo-voice-note.js`; `supabase/functions/transcribe-voice-note/index.ts`. | “A teacher may add a separate voice note and review its transcript before saving.” | “ContactLoop transcribes the parent call.” | 2, 3 |

## Claims that require qualification

- The live flow has been verified with a controlled test phone; do not generalize that result into universal reliability.
- Do not claim measured time savings until user research supplies a defensible measurement.
- Do not claim formal regulatory compliance.
- Do not present planned capabilities as current behavior.
- Do not describe AI-generated narrative as correct or final before teacher review.

