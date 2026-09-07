# Agents for Humans: AI Should Prepare the Record, Not Replace the Teacher's Judgment

Some information is easy for software to record. A call started at a particular time. It lasted a certain number of seconds. The provider returned “Connected” or “No Answer.”

Meaning is harder.

A teacher may begin a call intending to discuss attendance and end up talking about transportation, a schedule change, or a concern that requires careful follow-up. A parent may not answer at all. A note may be technically accurate but still lack the context another teacher would need before a meeting.

This is why I designed ContactLoop around a boundary: AI can prepare the record, but it should not replace the teacher's judgment.

## Intent is not evidence

ContactLoop asks a teacher to select a planned topic before making a call. That small action helps preserve why the outreach began.

But a planned topic is not evidence that a conversation occurred.

If a call is unanswered, busy, or failed, the system records an unsuccessful outreach attempt. It does not attach discussed topics to that event. It does not write a narrative implying that the teacher and parent talked about the planned subject.

If the call connects, the teacher can confirm the topics actually discussed. Keeping `planned topic` and `discussed topics` separate prevents a convenient assumption from becoming a false record.

This may sound like a data-model detail, but it is also a product principle: the system should make uncertainty visible instead of smoothing it into a confident sentence.

## Facts and interpretation need different paths

When ContactLoop prepares a Contact Brief, it combines several kinds of information. Some are operational facts: contact counts, outcomes, duration, and open follow-ups. Others are contextual: teacher notes, confirmed topics, concerns, resolutions, and possible next steps.

Those categories should not be handled in the same way.

Authoritative contact statistics come from a Supabase query rather than from model calculation. The Strands Agent retrieves teacher notes, confirmed discussed topics, and open follow-ups through narrow tools. A model accessed through Amazon Bedrock organizes supported context into a structured brief.

The model is useful because a meeting-ready summary is more than a database table. But its fluency cannot be treated as evidence. If the retrieved context does not support a concern, request, resolution, or follow-up, the system should leave that part empty rather than complete the pattern with something plausible.

The practical rule is simple:

> Let systems of record establish what happened. Let AI help organize what a human has actually confirmed.

## Review is a state, not a disclaimer

Many AI interfaces generate text and then add a small message asking users to verify it. That places the responsibility on the user without changing the workflow.

ContactLoop takes a different approach. Every generated Contact Brief begins as **Needs Teacher Review**.

The teacher can inspect the supporting contact history, edit the generated material, remove an incorrect interpretation, and add context. Only after that review can the brief become **Teacher Approved**.

This does not mean approval makes AI infallible. It means the product clearly identifies who has authority to finalize the material. The agent prepares; the teacher decides.

The same principle applies when a teacher chooses to add a voice note. That note is separate from the family call. Its transcript remains editable until the teacher confirms it. ContactLoop does not record parent calls or automatically transcribe family conversations.

Those limits are deliberate. More automation is not automatically better automation, especially when a workflow touches students, families, and sensitive context.

## Keeping the human work human

The purpose of ContactLoop is not to eliminate the teacher from family communication. It is to remove some of the remembering and organizing that surrounds it.

An unsuccessful attempt should remain visible without requiring another handwritten reminder. A connected call should be distinguishable from the teacher's original intent. An upcoming meeting should begin with organized context rather than a search through scattered notes. And a generated brief should pause at the point where professional judgment is required.

This is how I interpret **Agents for Humans**: the agent should carry routine work across systems, then surface when a person has a meaningful decision to make.

The human checkpoint is not a failure of autonomy. It is part of a well-designed agent.

## Three lessons for building responsible agents

Building ContactLoop left me with three principles that apply beyond education.

### 1. Keep tools narrow

Each tool should have one understandable responsibility. Retrieving authoritative statistics is different from retrieving narrative context, and both are different from finding unresolved work. Clear boundaries make the agent easier to inspect and the output easier to challenge.

### 2. Make uncertainty visible

Do not transform intent into evidence or an incomplete event into a finished story. Preserve distinctions such as attempted versus connected, planned versus discussed, and generated versus approved.

### 3. Preserve a real human decision point

If a person must review the result, represent that requirement in the product state and interaction flow. Give them the ability to edit, reject, add context, and approve. Do not hide human responsibility inside fine print.

AI is at its best here when it is useful without pretending to be authoritative. ContactLoop can prepare the material, preserve unfinished work, and reduce the effort required to recover context. But the teacher remains responsible for what the record means.

That boundary does not make the agent less capable. It makes the system more honest—and more worthy of the human relationships it is meant to support.

