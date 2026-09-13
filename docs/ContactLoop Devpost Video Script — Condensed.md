# ContactLoop — Devpost Demo Video Script (Condensed)

**Target length:** approximately 4 minutes  
**Hackathon:** Agents for Humans — Devpost

## 0:00–0:35 — Why I built ContactLoop

**On screen:** ContactLoop home page; speaker on camera, then transition to the product.

**Voiceover:**

Hi, I’m a teacher, and ContactLoop started with a question I asked another teacher I know.

She often got home almost two hours later than I did, so one day I asked, “Is the traffic really that bad?”

She told me traffic wasn’t the problem. She was staying late to finish documentation.

At first, I thought I should help teachers write faster. But what frustrated her most wasn’t writing. It was keeping track of parent calls.

Who did I call? Did they answer? What did we discuss? And who still needs follow-up?

That conversation became ContactLoop: a system that helps teachers make sure important family conversations don’t disappear.

## 0:35–0:55 — The promise

**On screen:** Click **Try Demo** and open Bella’s Dashboard.

**Voiceover:**

In the real Twilio flow, the telephony provider already knows the call outcome. The teacher shouldn’t have to document the same event again.

ContactLoop tracks calls, connects them to the right student and guardian, and keeps unfinished follow-ups visible.

On the Dashboard, Bella can see calls attempted, families reached, and follow-ups due. The question becomes: who needs my attention next?

## 0:55–1:35 — An unanswered call

**On screen:** Emma Johnson → **Call Parent** → Mom → **Behavior** → **Call Now**. Show the real test phone receiving the call, then return to ContactLoop.

**Voiceover:**

Let’s say Bella needs to contact Emma’s mom about a behavior concern. She selects Behavior and starts the call directly from ContactLoop.

For this recording, I’m using ContactLoop’s deterministic mock provider. The same provider interface is integrated with Twilio for real calls, without recording or playing conversation audio.

Emma’s mom doesn’t answer.

Bella does not manually create a call log or calculate which attempt this was. ContactLoop records the attempt, links it to Emma and her parent, updates the count, and keeps the follow-up visible.

That is the first key idea: document the calls automatically.

## 1:35–2:10 — A connected call

**On screen:** Lucas Smith → Dad → planned topic **IEP**. Show the connected result and duration. Select **IEP** and **Scheduling**, then add the note.

**Voiceover:**

Now Bella calls Lucas’s dad about an IEP meeting. ContactLoop captures the outcome and duration from the telephony provider automatically.

After the call, Bella confirms what was actually discussed. She selects IEP and Scheduling, then adds: “Dad confirmed Friday at 2 and asked about transportation.”

The reason for the call stays separate from the topics the teacher confirmed were discussed. The system never claims a conversation happened when a parent did not answer.

## 2:10–2:55 — Strands Agent and Contact Brief

**On screen:** Lucas’s Student Detail → **Generate AI Contact Summary**. Show Agent Activity and the resulting Contact Brief.

**Voiceover:**

Now ContactLoop has persistent communication history, not just a list of calls.

Bella can ask it to prepare a Contact Brief before a meeting or case review.

The Strands Agent uses three narrow ContactLoop tools: get_contact_stats, get_teacher_notes_and_topics, and get_open_follow_ups.

Amazon Bedrock turns that verified context into a brief with key topics, parent concerns, resolutions, open items, and a suggested next step.

The model does not guess numerical facts. Call counts, outcomes, durations, and follow-up totals come from deterministic Supabase queries. The agent organizes the teacher-confirmed context around those facts.

## 2:55–3:25 — Human in the loop

**On screen:** **Needs Teacher Review** → edit → optionally add a voice note → approve → **Teacher Approved**.

**Voiceover:**

But the AI does not get the final word.

Every brief begins as Needs Teacher Review. Bella can edit it, remove incorrect information, or add context. Teacher-created voice notes can be converted to text, but the transcript remains editable until she confirms it.

Only then does the brief become Teacher Approved.

AI summarizes. Teachers correct, add context, and decide.

## 3:25–3:50 — Follow-ups and impact

**On screen:** Follow-ups, then the approved Contact Brief or Meeting Brief.

**Voiceover:**

ContactLoop keeps unfinished follow-ups visible, so unsuccessful outreach does not disappear into phone history.

Before an IEP meeting or case review, teacher-approved records become a meeting-ready brief. Bella can see what was discussed, what was agreed, and what still needs attention.

## 3:50–4:15 — Closing

**On screen:** Simple architecture diagram, then return to the ContactLoop logo.

**Voiceover:**

Under the hood, a Vite-built Vanilla JavaScript frontend runs on Vercel. Supabase provides PostgreSQL, Auth, Row Level Security, and Deno Edge Functions. Twilio handles calling; a Python AWS Lambda runs Strands Agents, which uses narrow tools to read Supabase data, while Amazon Bedrock powers the Contact Brief.

Teacher voice notes use Google Cloud Storage and Speech-to-Text. ContactLoop does not record parent calls or automatically transcribe family conversations. Human control stays at the center.

ContactLoop is not here to replace a teacher’s relationship with families. It protects that relationship from getting lost in administrative noise.

That is what Agents for Humans means to me: AI handles the remembering and organizing, so people can stay focused on the human work.

Thank you.
