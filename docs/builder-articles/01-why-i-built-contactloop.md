# Agents for Humans: Why I Built ContactLoop for the Conversations Teachers Can't Afford to Lose

One day, I asked another teacher a question that sounded almost trivial: “Is the traffic really that bad?”

She often arrived home nearly two hours later than I did. I assumed the difference had something to do with her commute. It did not. She was staying at school to finish documentation.

My first instinct was to think about writing. Maybe teachers needed a faster way to produce notes. Maybe the answer was a better template or an AI writing assistant.

But as we talked, I realized that writing was only the visible part of the problem. The harder part was keeping track of family communication over time.

Who did I try to call? Did anyone answer? What was I planning to discuss? What did we actually discuss? Did the parent ask for something? Do I need to call again—and if so, when?

None of those questions is individually complicated. The burden comes from having to answer them across many students, many days, and many small interruptions.

## The work between the conversations

For a teacher, contacting a family is not a single action. It is a loop.

A teacher decides that a conversation is needed. They find the right contact, make an attempt, and then document the result. If no one answers, the attempt still matters, and the teacher needs to remember to try again. If a conversation does happen, the teacher needs to preserve enough context to prepare for the next meeting without turning a human relationship into a pile of disconnected notes.

The phone already knows that a call happened. Yet the teacher is often asked to reconstruct that event somewhere else.

That duplication is easy to underestimate. A single extra entry may take only a minute. But the real cost is not just time. It is attention. Every manual handoff creates another opportunity for an unsuccessful attempt to disappear, an open follow-up to be forgotten, or an important piece of context to become difficult to find.

This is the problem that became ContactLoop.

## Not another place to type

I did not want to build one more blank text box for teachers to manage.

ContactLoop is designed around continuity. A call can begin inside the product. Its result returns to the contact history and is associated with the relevant student and guardian. If the outreach is unsuccessful, the follow-up remains visible. If a call connects, the teacher can confirm what was actually discussed and add the context that only a person in the conversation can provide.

Before a meeting or case review, that history can become a Contact Brief: a structured view of contact activity, key topics, teacher notes, and unresolved items. The brief begins as **Needs Teacher Review**. It is not treated as final until the teacher has had the opportunity to correct it, add context, and approve it.

That distinction matters. ContactLoop does not record parent calls or automatically transcribe family conversations. It should not pretend to know what happened inside a conversation. It can preserve the surrounding facts and organize teacher-confirmed context, but the teacher remains the authority on meaning.

## Why this needs an agent

The repetitive work here is not simply generating a paragraph. It is gathering the right pieces of information, separating attempts from completed conversations, identifying what is still unresolved, and preparing something useful for review.

That is why I began thinking about ContactLoop as an agent rather than a writing feature.

The goal is not to create another application that demands attention. The goal is to let the system handle the background work and surface itself when a teacher has a real decision to make: confirm a discussed topic, add missing context, approve a brief, or complete a follow-up.

The technology should become quieter as the human work becomes clearer.

## Protecting the relationship from administrative noise

Family communication in education is not a transaction to optimize away. Teachers build trust through repeated, sometimes difficult conversations. The administrative record is important, but it should support that relationship instead of competing with it.

ContactLoop is my attempt to protect the continuity of those conversations.

It remembers that an attempt happened. It keeps unfinished work visible. It prepares context for the teacher to review. It does not replace the teacher's judgment, and it does not turn a sensitive conversation into an automatic conclusion.

When I think about the phrase **Agents for Humans**, this is what it means to me: AI handles the remembering and organizing so that people can stay focused on the work that requires empathy, judgment, and trust.

For teachers, the most important part of a family conversation will always be the human connection. ContactLoop is there to make sure that connection does not get lost in the administrative noise around it.

ContactLoop is my submission to the AWS Agents for Humans Hackathon. The [source code is available on GitHub](https://github.com/spatblan4/ContactLoop).
