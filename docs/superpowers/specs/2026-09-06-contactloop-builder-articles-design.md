# ContactLoop AWS Builder Article Series Design

**Date:** 2026-09-06  
**Hackathon:** AWS Agents for Humans  
**Publication platform:** builder.aws.com  
**Planned publication date:** 2026-09-13

## Objective

Publish three complementary English articles that document the motivation, implementation, and human-in-the-loop principles behind ContactLoop. Each article should qualify for the hackathon's optional Builder content bonus while also strengthening the project's story for judges.

The series must explain the value of ContactLoop without exposing unreleased product plans, complete prompts, secrets, or a copyable blueprint of its business logic.

## Audience and Voice

The primary audience is the Agents for Humans judging community and AWS builders interested in practical agent systems. The articles will use the founder's first-person voice as a teacher who discovered the problem through another teacher's experience.

The tone should be personal, concrete, technically credible, and restrained. It should avoid marketing exaggeration and distinguish verified implementation from future possibilities.

## Publication Strategy

All three drafts will be completed and fact-checked before publication. They should be published together on September 13, 2026, leaving time to verify public URLs and add them to the Devpost submission before the September 14, 2026, 5:00 PM PDT deadline.

Each title will contain the exact phrase `Agents for Humans`. Each article will link to the public ContactLoop repository or Devpost submission when those URLs are ready.

## Article 1: Problem and Origin Story

### Working title

**Agents for Humans: Why I Built ContactLoop for the Conversations Teachers Can't Afford to Lose**

### Purpose

Establish the authentic problem insight and emotional reason for building ContactLoop without disclosing the full implementation blueprint.

### Target length

700–900 words.

### Structure

1. A fellow teacher regularly arrived home almost two hours later.
2. The cause was not traffic but documentation after the school day.
3. The deeper burden was not writing speed; it was remembering family contacts over time.
4. Missed calls, discussed topics, and unfinished follow-ups easily disappear across separate systems and personal notes.
5. ContactLoop's promise is to preserve the continuity of important family conversations.
6. Explain at a high level why this is more than another note-taking or chat application.
7. Briefly show the outcome: calls are connected to the correct student and guardian, unresolved follow-ups remain visible, and meeting preparation begins from a reliable contact history.
8. Close with the principle that AI should handle remembering and organizing so teachers can focus on relationships.

### Disclosure boundary

This article may disclose the problem, founder story, mission, target user, and high-level outcome. It must not disclose detailed architecture, prompts, tool schemas, internal decision rules, the complete feature map, commercial strategy, or unreleased roadmap.

## Article 2: Technical Build

### Working title

**Agents for Humans: Building ContactLoop with Strands Agents, Amazon Bedrock, Twilio, and Supabase**

### Purpose

Demonstrate a genuine, non-trivial Strands Agents implementation and explain how the production components form an end-to-end workflow.

### Target length

1,100–1,400 words.

### Structure

1. Explain why a general chat interface is insufficient for persistent contact tracking.
2. Present the end-to-end ContactLoop data flow.
3. Explain how Twilio initiates a real call and returns its status to ContactLoop.
4. Explain how Supabase stores authoritative contact events, outcomes, durations, notes, and follow-up state.
5. Introduce the Strands Agent and its three narrow tool responsibilities:
   - retrieving authoritative contact statistics;
   - retrieving teacher notes and discussed topics;
   - retrieving open follow-ups.
6. Explain how Amazon Bedrock turns verified tool output into a contextual Contact Brief.
7. Explain why numerical claims come from database queries rather than model inference.
8. Show the `Needs Teacher Review` state and approval flow.
9. Summarize implementation lessons: narrow tools, separation of facts from narrative, and explicit human authority.

### Disclosure boundary

The article may describe component responsibilities, the high-level architecture, the existence and purpose of agent tools, and the demonstrated workflow. It must not publish credentials, service-role keys, full prompts, complete tool payloads, sensitive test data, or all internal business rules.

## Article 3: Trust and Human Judgment

### Working title

**Agents for Humans: AI Should Prepare the Record, Not Replace the Teacher's Judgment**

### Purpose

Explain the product principles that make ContactLoop appropriate for a sensitive education setting and translate those principles into reusable lessons for agent builders.

### Target length

800–1,000 words.

### Structure

1. Explain why family communication records contain context that software cannot safely assume.
2. Separate a planned topic from topics a teacher confirms were actually discussed.
3. Explain why a missed call must never be narrated as a conversation.
4. Separate database facts from model interpretation.
5. Explain why every generated Contact Brief begins as `Needs Teacher Review`.
6. Show how a teacher edits, adds context, and approves the brief.
7. State the product boundary: ContactLoop does not record parent calls or automatically transcribe family conversations.
8. Define what "Agents for Humans" means in this education workflow.
9. End with three transferable lessons for agent developers.

### Disclosure boundary

The article may explain safety principles, review states, and product boundaries. It must not imply legal or regulatory compliance that has not been independently established, promise error-free AI output, or reveal unreleased safeguards as if they already exist.

## Verified Claims Available to the Series

The following claims are supported by the current project and may be used:

- ContactLoop can initiate a real Twilio call to a controlled test phone.
- Call results can be returned to and stored by ContactLoop.
- Contact events are associated with a student and guardian.
- The system distinguishes a planned call topic from teacher-confirmed discussed topics.
- Unfinished follow-ups remain visible.
- The AWS provider uses Strands Agents SDK and Amazon Bedrock.
- The agent retrieves authoritative information through narrow tools rather than asking the model to invent counts.
- Supabase stores persistent communication data.
- Generated Contact Briefs begin in a pending teacher-review state.
- Teachers can edit and approve AI-generated material.
- ContactLoop does not record parent calls or automatically transcribe family conversations.

## Claims to Avoid or Qualify

- Do not claim that live cloud integrations are universally reliable based only on a controlled demonstration.
- Do not claim measurable time savings unless supported by collected user data.
- Do not claim FERPA, COPPA, GDPR, or other formal compliance without an appropriate review.
- Do not imply that ContactLoop understands the contents of a phone call automatically.
- Do not present planned features as implemented features.
- Do not claim that AI output is correct before teacher review.

## Visual Assets

Use a small number of screenshots that prove the workflow rather than reveal every feature:

- Article 1: dashboard or follow-up view.
- Article 2: architecture diagram, call result, and Agent Activity or Contact Brief view.
- Article 3: `Needs Teacher Review` and `Teacher Approved` states.

Screenshots must use demo data and must not expose real student, guardian, phone, credential, or service information.

## Acceptance Criteria

- The three articles cover distinct story, engineering, and trust angles without repeating the same introduction.
- Every title includes `Agents for Humans`.
- Every factual product claim is traceable to the repository, a verified live flow, or the user's direct confirmation.
- The founder story remains personal but does not disclose the product's complete blueprint.
- No secrets, private data, full prompts, unsupported metrics, or unverified compliance claims appear.
- The articles are complete English drafts ready for user fact-checking and Builder publication.
- Public links are verified and added to Devpost before the submission deadline.
