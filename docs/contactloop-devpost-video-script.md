# ContactLoop — Devpost Demo Video Script

**Target length:** approximately 4 minutes

**Recording note:** Use fictional students and guardians. During the call step, show the real test phone receiving the call for a few seconds. Do not play call audio or show private notifications.

## 0:00–0:40 — Why I built ContactLoop

**On screen:** ContactLoop home page. Speaker on camera, then transition to the product.

**Voiceover:**

Hi, I’m a teacher, and ContactLoop started with a question I asked another teacher I know.

She often got home almost two hours later than I did, so one day I asked her, “Is the traffic really that bad?”

She told me traffic wasn’t the problem. She was staying late to finish documentation.

At first, I thought I should build something to help teachers write faster. But when I asked what frustrated her most, her answer surprised me.

It wasn’t writing. It was keeping track of parent calls.

Who did I call? Did they answer? What did we discuss? And who still needs follow-up?

That conversation became ContactLoop: a communication system designed to help teachers make sure important family conversations don’t disappear.

## 0:40–0:58 — The product promise

**On screen:** Click **Try Demo** and open Bella’s Dashboard. Briefly show the main metrics.

**Voiceover:**

The idea is simple: in the real Twilio flow, the telephony provider already knows the call outcome. The teacher shouldn’t have to document the same event again.

ContactLoop automatically tracks calls, connects them to the right student and guardian, and keeps unfinished follow-ups visible.

On the Dashboard, Bella can immediately see calls attempted, families reached, and follow-ups due.

The question becomes: who needs my attention next?

## 0:58–1:45 — Demo: a call that isn’t answered

**On screen:** Open Emma Johnson → **Call Parent** → Mom → select **Behavior** → **Call Now**. Show the real test phone receiving the call. End the call or let it go unanswered, then return to ContactLoop.

**Voiceover:**

Let’s say Bella needs to contact Emma’s mom about a behavior concern.

Before calling, she can optionally select why she is reaching out. I’ll choose Behavior.

Now she starts the call directly from ContactLoop.

For this recording, I’m using ContactLoop’s deterministic mock provider. The same provider interface is integrated with Twilio for real calls. In either case, ContactLoop shows the workflow without recording or playing conversation audio.

Emma’s mom doesn’t answer.

Bella does not manually create a call log, type the time, enter the outcome, or calculate which attempt this was. ContactLoop records the attempt, links it to Emma and her parent, updates the attempt count, and keeps the follow-up visible.

When we return to the Dashboard, the data has already changed.

That is the first key idea behind ContactLoop: document the calls automatically.

## 1:45–2:25 — Demo: a connected call

**On screen:** Open Lucas Smith → Dad → planned topic **IEP** → start the call → show the connected result and duration. Select discussed topics **IEP** and **Scheduling**, then add the note.

**Voiceover:**

Now let’s look at a connected call.

Bella calls Lucas’s dad about an IEP meeting. ContactLoop captures the outcome and duration from the telephony provider automatically.

After the call, Bella confirms what was actually discussed. She selects IEP and Scheduling, then adds a short note:

“Dad confirmed Friday at 2 and asked about transportation.”

ContactLoop keeps the reason for the call separate from the topics the teacher confirmed were discussed. The system never claims a conversation happened when a parent did not answer.

## 2:25–3:15 — Strands Agent and the Contact Brief

**On screen:** Open Lucas’s Student Detail → **Generate AI Contact Summary**. Show Agent Activity, then the resulting Contact Brief.

**Voiceover:**

Now ContactLoop has something more valuable than a list of phone calls: persistent communication history.

Bella can ask ContactLoop to prepare a Contact Brief for Lucas before a meeting or case review.

This is where the Strands Agent comes in.

The agent receives the student and date range, then calls three narrow ContactLoop tools: get_contact_stats, get_teacher_notes_and_topics, and get_open_follow_ups. It does not receive unrestricted database access.

Amazon Bedrock then helps turn that verified context into a structured brief.

The result includes key topics, parent concerns, resolutions, open items, and a suggested next step.

The model does not guess numerical facts. Call counts, outcomes, durations, and follow-up totals come from deterministic database queries. The agent organizes the teacher-confirmed context around those facts.

## 3:15–3:45 — Human in the loop

**On screen:** Show **Needs Teacher Review** → edit the brief → optionally add a voice note → approve. Show **Teacher Approved**.

**Voiceover:**

But the AI still doesn’t get the final word.

Every generated brief begins as Needs Teacher Review. Bella can edit it, remove incorrect information, or add context.

She can also add context using her own voice note. ContactLoop transcribes that teacher-created note, and the transcript remains editable until she reviews and confirms it.

Only then does the brief become Teacher Approved.

AI summarizes. Teachers correct, add context, and decide.

## 3:45–4:10 — Follow-ups and meeting readiness

**On screen:** Open Follow-ups, then show the Meeting Brief or approved Contact Brief.

**Voiceover:**

ContactLoop keeps unfinished follow-ups visible, so an unsuccessful outreach attempt does not disappear into phone history.

Before an IEP meeting or case review, teacher-approved records become a meeting-ready brief. Bella can immediately see what was discussed, what was agreed, and what still needs attention.

## 4:10–4:35 — How it works and closing

**On screen:** First show the workflow-loop slide. Then switch to the “Why each layer exists” slide, before returning to the ContactLoop logo and slogan.

**Voiceover:**

This is the ContactLoop workflow. Once a teacher approves a brief, it becomes useful context for the next time she reaches out.

Supabase keeps the communication history, and Twilio reports what happened on the call. In AWS Lambda, a Strands Agent gathers the relevant stats, notes, and follow-ups. Amazon Bedrock turns that context into a draft Contact Brief.

But the teacher still has the last word. She can edit it, add context, and decide what belongs in the final record.

That is why these five layers exist: the system remembers what happened, AI helps organize the context, and the teacher decides what becomes the record.

ContactLoop does not record parent calls or automatically transcribe family conversations. Human control stays at the center.

ContactLoop is not here to replace the teacher’s relationship with families.

It is here to protect that relationship from getting lost in administrative noise.

That is what Agents for Humans means to me: AI handles the remembering and organizing, so people can stay focused on the human work.

Thank you.
