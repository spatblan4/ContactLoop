# Strands Outreach Plan Design

> **Superseded architecture (2026-09-07):** The external Outreach Lambda/service described below was retired before submission. The active implementation runs the real Strands Agent inside FastAPI at `backend/app/services/outreach_plan_agent.py` and calls Amazon Bedrock directly. The existing Contact Brief Lambda remains unchanged.

## Goal

Add a teacher-reviewed, daily outreach plan to ContactLoop. A Strands Agent will turn a teacher's existing contact history, approved notes, and open follow-ups into a prioritized list of students to contact and suggested next steps.

## Product Scope

ContactLoop remains a tool for special education teachers to track parent calls. The new feature does not place calls, send messages, or change records without a teacher's explicit confirmation.

The Dashboard will show a prepared `Today's Outreach Plan` for the demo. A `Refresh with Agent` action will run the live Strands/Bedrock flow and replace the plan with a newly generated, teacher-reviewable result. Each recommendation offers `Review` and, when relevant, `Create follow-up` actions.

## Architecture

The browser authenticates to the FastAPI backend. FastAPI is the only browser-facing route for data and authorizes every request against the signed-in teacher. The backend uses Supabase Postgres as its production database; this is the same source of truth used by the Strands/Bedrock service.

The Strands service receives only the authorized outreach context needed for a plan. Its tools return contact statistics, approved teacher notes and topics, and open follow-ups. The service never receives browser credentials, and AWS, Supabase service-role, and Bedrock credentials remain server-side.

```text
Browser -> FastAPI (teacher authorization) -> Supabase Postgres
                         |
                         -> Strands/Bedrock Agent -> teacher-reviewed outreach plan
```

## Agent Behavior

For the authenticated teacher's active students, the Agent prioritizes outreach using the supplied facts. It may describe a suggested follow-up time, but it must not invent concerns, outcomes, promises, or topics. It must label missing evidence rather than infer it.

The Agent returns ordered plan items with a student reference, an evidence-grounded reason, and a suggested next step. The resulting plan is a draft. A teacher must review an item before a follow-up record is created or changed.

## Demo and Production Behavior

Demo mode starts with seeded plan content so the value is visible immediately. The live `Refresh with Agent` path must remain available and will be used in the hackathon video to demonstrate real Strands execution.

The production version uses the same plan generation flow. Scheduled daily refresh is explicitly out of scope for this deadline; the product may add it after the hackathon without changing the review model.

## Failure Handling

If the Agent request fails or times out, ContactLoop retains the most recent successful plan and displays a clear retry message. Existing student records, contact history, and follow-ups stay usable. No agent failure may create or modify a follow-up.

## Verification

Automated coverage will verify authorization boundaries, no-candidate handling, normalized Agent plan output, failure behavior, and teacher-confirmed follow-up creation. A live verification will call the existing Strands/Bedrock endpoint with non-sensitive demo data. The hackathon handoff also requires a public repository, README, open-source license, architecture diagram, live demo URL when available, and a five-minute demonstration video.

## Explicit Non-Goals

- Automated calling, texting, or email.
- Automatic database changes from the Agent.
- A separate data store for Agent results.
- Moving secrets into the browser or repository.
- Scheduled background execution before the hackathon deadline.
