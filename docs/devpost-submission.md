# ContactLoop

## One-line pitch

**A teacher-first communication workspace that turns repeated family outreach into a reliable loop of contact, follow-up, context, and human-reviewed AI preparation.**

## Inspiration

Family communication is rarely one clean conversation. A teacher may call, reach voicemail, try again, leave a note, promise a follow-up, and later prepare for a meeting. The information is important, but it is scattered across tools and memory. ContactLoop began with a simple question: what if the entire outreach loop stayed visible without asking AI to replace teacher judgment?

## What it does

ContactLoop gives teachers one workspace for students, guardians, outreach, and follow-up. A teacher can start a real phone call, preserve its outcome, keep an unsuccessful attempt open as a follow-up, and record what was planned separately from what was actually discussed.

When a teacher needs a concise view, the ContactLoop agent prepares a structured Contact Brief from authoritative contact statistics, teacher notes and topics, and unresolved follow-ups. The brief is marked as needing teacher review. The teacher can edit and approve it before it becomes final.

This makes ContactLoop an agent for preparation and continuity—not an autonomous decision-maker.

## How we built it

The frontend is a Vite single-page application with a public Demo mode and a private authenticated Beta mode. Supabase provides authentication, relational storage, database functions, and Edge Functions. Twilio starts outbound calls and sends status updates back to the contact record.

The AI provider is built with the **Strands Agents SDK** and **Amazon Bedrock**. It exposes three deliberately narrow, read-only tools:

1. `get_contact_stats` for authoritative counts and rates.
2. `get_teacher_notes_and_topics` for teacher-authored context.
3. `get_open_follow_ups` for unresolved outreach.

The provider can run in an AWS Lambda-compatible service. Server credentials remain outside the browser, and the response is structured JSON with `review_status: "pending"`. ContactLoop's human-in-the-loop editor is the final boundary before approval.

## Challenges we ran into

The hardest challenge was preserving truth across a messy real-world workflow. A planned topic is not automatically a discussed topic. A started phone call is not automatically a connected conversation. A generated summary is not automatically an approved record.

We addressed those distinctions in the data model and UI instead of hiding them in prompt wording. We also separated provider responsibilities: Twilio owns telephony status, Supabase owns the operational record, and the AWS agent prepares a brief from read-only evidence.

## Accomplishments that we're proud of

- Ran a real Twilio call end to end and wrote the result back to the correct contact record.
- Kept missed outreach visible through open follow-ups rather than treating an attempt as completion.
- Built a Strands/Bedrock agent with narrow tools and structured output.
- Added a teacher edit, review, and approval flow for AI-generated briefs.
- Maintained separate Demo and authenticated Beta paths in one codebase.
- Added automated tests for core domain rules, provider boundaries, and telephony status handling.

## What we learned

Human-centered agents need stronger boundaries, not just better prose. The quality of a Contact Brief depends on where each fact came from, whether a call really connected, and whether the responsible person reviewed the result. We learned to make those states visible in the product and explicit in the agent contract.

We also learned that agentic software is most useful when it removes preparation work while preserving professional judgment. For teachers, trust is a product feature.

## What's next for ContactLoop

Next, we want to validate the workflow with more teachers, improve accessibility and multilingual family communication, expand deployment hardening, and evaluate Amazon Bedrock AgentCore where it materially improves observability and operations. We also want to measure whether ContactLoop reduces missed follow-ups and meeting-preparation time without increasing documentation burden.

## Links

- Source: https://github.com/spatblan4/ContactLoop
- Submission working file: `public/contactloop-submission-center.html`
