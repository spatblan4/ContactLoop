# Agents for Humans: Building ContactLoop with Strands Agents, Amazon Bedrock, Twilio, and Supabase

When I began building ContactLoop, I was not trying to make a chatbot for teachers. The problem I wanted to solve was more operational: family outreach creates a trail of small tasks that must stay connected over time.

A teacher may plan a call, reach the wrong moment, try again later, complete the conversation, add context, and carry an unresolved item into a future meeting. A useful system has to do more than answer a question about that process. It has to work across the process.

That distinction shaped the architecture of ContactLoop. Twilio handles real-world calling. Supabase stores persistent contact facts. A Strands Agent retrieves the right context through narrow tools, and a model accessed through Amazon Bedrock prepares a structured Contact Brief. The teacher reviews the result before it becomes approved material.

## From a phone call to persistent context

The first part of the workflow begins before AI is involved.

A teacher selects a student, the relevant guardian, and a planned topic. ContactLoop then initiates a real call through Twilio. I tested this flow with a phone that I control: the phone rings, the call completes or goes unanswered, and the result returns to ContactLoop.

This matters because the system should not ask a teacher to recreate information that already exists. The call provider knows whether an attempt was connected, unanswered, busy, or failed. ContactLoop connects that result to the correct student and guardian and stores it as part of the communication history.

The planned topic is stored as intent. It is not automatically treated as the content of the conversation. If the call does not connect, ContactLoop records an unsuccessful outreach attempt. If it does connect, the teacher can confirm the topics actually discussed and add a note.

That separation became one of the most important data decisions in the project. “I planned to discuss an IEP meeting” and “we discussed an IEP meeting” are different claims. A reliable agent needs the data model to preserve that difference before a language model ever sees the information.

## Supabase as the source of contact facts

ContactLoop uses Supabase for persistent workflow data: students, guardians, contact events, outcomes, durations, teacher-confirmed topics, notes, and follow-ups.

When an outreach attempt is unsuccessful, an open follow-up keeps the unfinished work visible. A later connected contact can resolve the stale action in the working view. The goal is not to produce more records; it is to make the current state understandable.

Supabase also has a second responsibility in the AI workflow: it provides authoritative numbers.

Language models are useful for organizing context, but they should not be asked to infer a count that the database can calculate directly. Contact statistics therefore come from a dedicated Supabase RPC. The service validates those values and attaches them to the response separately from the generated narrative.

This gives the system a clear rule:

> Queries establish the measurable facts. The model organizes the supported context around them.

## Giving the Strands Agent narrow tools

The Contact Brief provider uses the Strands Agents SDK with a model through Amazon Bedrock. Instead of exposing the entire database or asking the model to reason from a large unstructured dump, I gave the agent three narrow tool responsibilities:

1. Retrieve authoritative contact statistics for one student and date range.
2. Retrieve teacher notes and confirmed discussed topics for that period.
3. Retrieve currently open follow-ups for that student.

Each tool answers a specific kind of question. This makes the agent's work easier to inspect and reduces the chance that unrelated data enters the brief.

The agent must call the tools before generating the result. It uses notes and confirmed topics as narrative evidence and uses open follow-ups for unresolved items. The output follows a structured Contact Brief schema rather than returning a free-form essay.

The high-level flow looks like this:

```text
Teacher action → ContactLoop → Twilio call/status
                         ↓
                    Supabase facts
                         ↓
               Strands Agent tools
                         ↓
                 Amazon Bedrock
                         ↓
             Reviewable Contact Brief
                         ↓
                  Teacher approval
```

The browser sends only the selected student, date range, and whether teacher notes should be included. The server-side provider retrieves the permitted context and keeps privileged database access away from the browser.

This boundary is important for both security and product clarity. The interface requests a brief. It does not receive database credentials, construct authoritative statistics, or decide which internal records count as evidence.

## What Amazon Bedrock does—and does not do

The model's job is to turn retrieved context into a concise, useful structure. A Contact Brief can include key topics, parent concerns that are actually supported by teacher-confirmed notes, resolutions, unresolved items, and a suggested next step.

The model does not calculate call totals. It does not invent missing concerns. It does not convert a planned topic from an unanswered call into something that was discussed. If evidence for a field is missing, the appropriate result is an empty field, not a plausible guess.

These constraints are not only prompt instructions. They are reflected in how information is separated before generation. Statistics, notes, discussed topics, and follow-ups enter the workflow through distinct paths, and the response keeps authoritative stats separate from generated narrative.

That is a lesson I will carry into future agent projects: prompting matters, but data boundaries matter first.

## The teacher remains the final decision point

Every generated brief returns with a pending review status. In the interface, it appears as **Needs Teacher Review**.

The teacher can edit the narrative, remove an incorrect interpretation, or add context that was not available to the agent. A teacher may also add a separate voice note and review the resulting transcript before saving it. This is different from recording or transcribing the parent call; ContactLoop does neither.

Only after review does the brief become **Teacher Approved**.

This changes the role of the agent. It is not an authority producing an official account of a family conversation. It is a worker preparing organized material for the person who has the context and responsibility to decide what is accurate.

## What I learned from building the workflow

Three implementation lessons became especially clear.

First, give an agent narrow tools with explicit responsibilities. A small tool surface makes it easier to reason about where every claim came from.

Second, keep facts and narrative separate. Counts, outcomes, and timestamps belong to deterministic queries. A model can help organize teacher-confirmed context, but it should not manufacture operational truth.

Third, make human authority part of the workflow rather than a disclaimer at the bottom of the screen. **Needs Teacher Review** is not warning text added after generation. It is a real product state with an edit-and-approve path.

ContactLoop is still focused on a simple promise: important family communication should not disappear into administrative noise. Strands Agents helps coordinate the work needed to prepare context, Amazon Bedrock helps shape that context into a useful brief, and the surrounding system preserves the facts and decisions that belong to people.

For me, that is the value of an agent for humans. It does real work across tools, but it also knows where its work should stop.

