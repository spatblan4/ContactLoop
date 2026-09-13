# ContactLoop Demo Script — Updated Readable Version

Target length: about 4 minutes

## 0:00–0:40 — Why I built ContactLoop

**On screen:** ContactLoop home page, then the product.

Hi, I’m a teacher, and ContactLoop started with a question I asked another teacher I know.

She often got home almost two hours later than I did, so one day I asked her, “Is the traffic really that bad?”

She told me traffic wasn’t the problem. She was staying late to finish documentation.

At first, I thought I should build something to help teachers write faster. But what frustrated her most wasn’t writing. It was keeping track of parent calls.

Who did I call? Did they answer? What did we discuss? And who still needs follow-up?

That conversation became ContactLoop, a communication system designed to make sure important family conversations don’t disappear.

## 0:40–0:58 — The promise

**On screen:** Open Bella’s Dashboard and show the main metrics.

In the real Twilio flow, the telephony provider already knows the call outcome. The teacher shouldn’t have to document the same event again.

ContactLoop automatically tracks call attempts and outcomes, connects them to the right student and guardian, and keeps unfinished follow-ups visible.

On the Dashboard, Bella can see calls attempted, families reached, and follow-ups due. The question becomes: who needs my attention next?

## 0:58–1:45 — An unanswered call

**On screen:** Emma Johnson → Call Parent → Mom → Behavior → Call Now.

Let’s say Bella needs to contact Emma’s mom about a behavior concern. She selects Behavior and starts the call from ContactLoop.

For this recording, I’m using ContactLoop’s deterministic mock telephony provider. The same provider interface is integrated with Twilio for real calls. ContactLoop does not record or play conversation audio.

Emma’s mom doesn’t answer.

Bella does not manually create a call log, type the time, enter the outcome, or calculate which attempt this was. ContactLoop records the attempt, links it to Emma and her parent, updates the attempt count, and keeps the follow-up visible.

That is the first key idea: document the call automatically.

## 1:45–2:25 — A connected call

**On screen:** Lucas Smith → Dad → planned topic IEP → show Connected and duration → select IEP and Scheduling → add note.

Now Bella calls Lucas’s dad about an IEP meeting. ContactLoop captures the outcome and duration from the telephony provider automatically.

After the call, Bella confirms what was actually discussed. She selects IEP and Scheduling, then adds: “Dad confirmed Friday at 2 and asked about transportation.”

The reason for the call stays separate from the topics the teacher confirmed were discussed. The system never claims a conversation happened when a parent did not answer.

## 2:25–3:15 — Strands Agent and Contact Brief

**On screen:** Lucas’s Student Detail → Generate AI Contact Summary. Show Agent Activity and the result.

Now ContactLoop has persistent communication history, not just a list of phone calls.

Bella can ask it to prepare a Contact Brief before a meeting or case review.

The Strands Agent receives the student and date range, then calls three narrow ContactLoop tools:

```text
get_contact_stats
get_teacher_notes_and_topics
get_open_follow_ups
```

It does not receive unrestricted database access. Amazon Bedrock provides the Claude model that turns the retrieved context into a structured brief.

The result includes key topics, parent concerns, recorded resolutions, open items, and a suggested next step.

The model does not guess numerical facts. Call counts, outcomes, durations, and follow-up totals come from deterministic Supabase queries. The agent organizes the teacher-confirmed context around those facts.

## 3:15–3:45 — Human in the loop

**On screen:** Needs Teacher Review → edit → add a voice note → approve → Teacher Approved.

But the AI does not get the final word.

Every generated brief begins as Needs Teacher Review. Bella can edit it, remove incorrect information, or add context.

She can also add context using her own voice note. ContactLoop transcribes that teacher-created note, and the transcript remains editable until she reviews and confirms it.

Only then does the brief become Teacher Approved.

AI summarizes. Teachers correct, add context, and decide.

## 3:45–4:10 — Follow-ups and meeting readiness

**On screen:** Follow-ups, then the approved Contact Brief or Meeting Brief.

ContactLoop keeps unfinished follow-ups visible, so unsuccessful outreach does not disappear into phone history.

Before an IEP meeting or case review, teacher-approved records become a meeting-ready brief. Bella can see what was discussed, what was agreed, and what still needs attention.

## 4:10–4:30 — How it works and closing

**On screen:** Architecture diagram, then the ContactLoop logo.

Under the hood, a Vite-built Vanilla JavaScript frontend runs on Vercel. Supabase provides PostgreSQL, Auth, Row Level Security, and Deno Edge Functions. Twilio handles calling. A Python AWS Lambda runs Strands Agents, which uses narrow read-only tools to retrieve Supabase data. Amazon Bedrock provides the Claude model.

Teacher voice notes use a signed upload to Google Cloud Storage and Google Speech-to-Text before review. ContactLoop does not record parent calls or automatically transcribe family conversations.

Human control stays at the center.

ContactLoop is not here to replace a teacher’s relationship with families. It protects that relationship from getting lost in administrative noise.

That is what Agents for Humans means to me: AI handles the remembering and organizing, so people can stay focused on the human work.

Thank you.
