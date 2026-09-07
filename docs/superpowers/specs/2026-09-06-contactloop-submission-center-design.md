# ContactLoop Submission Center Design

**Date:** 2026-09-06  
**Artifact:** Standalone HTML submission dashboard  
**Primary file:** `docs/contactloop-submission-center.html`  
**Published copy:** `public/contactloop-submission-center.html`

## Purpose

Create one self-contained page that helps the user finish and review the AWS Agents for Humans submission. The page combines an evidence-based final delivery checklist with three collapsible AWS Builder article drafts.

The page is a private working tool, not a public marketing page. It must be useful when opened directly from the filesystem and must not require a build step, framework, external font, or network connection.

## Information Architecture

The page has four major regions:

1. A compact hero with the ContactLoop name, hackathon name, deadline, and overall completion percentage.
2. A grouped submission checklist covering eligibility/accounts, product workflow, technical materials, repository, Devpost, demo video, and bonus content.
3. A readiness summary that distinguishes verified items from user-managed pending items.
4. A three-article library with one collapsible panel per AWS Builder draft.

The checklist appears before the articles because it is the operational focus of the page. Articles remain fully embedded so the file works offline.

## Checklist Behavior

Each checklist item has:

- a stable identifier;
- Chinese action text;
- a short evidence or next-step note;
- a group label;
- an initial status;
- an optional local file or public URL.

Items with repository or workflow evidence begin checked. Items that depend on the user's external accounts, publication, upload, deployment, or final submission begin unchecked unless there is direct evidence in the project.

User changes persist in `localStorage` under a versioned key. Saved state overrides the initial state on future visits. A reset control restores the evidence-based defaults after confirmation.

The progress indicator is calculated from checked items divided by total items. It updates immediately and shows both percentage and completed count. Completing every checkbox changes the summary to a final-ready state; the page must not claim readiness while items remain unchecked.

## Checklist Groups

### Eligibility and accounts

- Join the Devpost hackathon.
- Confirm individual or team representation.
- Confirm eligibility and age requirements.
- Prepare an AWS account.
- Prepare an AWS Builder ID.
- Select the Good Neighbor Agents track.

These begin unchecked because they depend on external account state or the user's final choice.

### Working product

- Define a specific teacher audience and repetitive communication problem.
- Demonstrate real Twilio calling.
- Demonstrate call result write-back.
- Associate events with the correct student and guardian.
- Keep unsuccessful outreach visible as an open follow-up.
- Keep planned and discussed topics separate.
- Generate a Contact Brief through Strands Agents and Amazon Bedrock.
- Require teacher review and approval.
- Include basic error handling.

These begin checked where repository code, tests, documentation, and the user's live-flow confirmation provide evidence.

### Technical materials

- Use Strands Agents SDK in the core workflow.
- Prepare an architecture diagram.
- Document AWS services and third-party services.
- Keep service credentials server-side.
- Prepare reproducible setup and test instructions.
- Decide whether to deploy with Amazon Bedrock AgentCore.
- Prepare and verify a public live demo.

Items supported by the repository begin checked. AgentCore and final live-demo verification begin unchecked.

### Public repository

- Make the repository public.
- Include complete source code and required assets.
- Provide an English README with setup instructions.
- Add an MIT or Apache license visible to Devpost.
- Disclose work that existed before the submission period.
- Remove secrets and private student information.

Only items directly verifiable from the current repository begin checked. Repository visibility, license visibility, final README completeness, and disclosure begin unchecked until explicitly verified.

### Devpost submission

- Write the English project description.
- Add project name and one-line pitch.
- Upload logo, cover image, and screenshots.
- Add the public repository URL.
- Add the architecture diagram.
- Add AWS Builder ID.
- Select the track.
- Add live demo and testing instructions.
- Add all published Builder article URLs.
- Submit before September 14, 2026, 5:00 PM PDT.

These begin unchecked because the actions occur on Devpost.

### Demo video

- Finalize the English script.
- Record the real end-to-end workflow.
- Show problem, audience, and why it matters.
- Show Strands tools and AWS architecture.
- Show teacher review and approval.
- Keep the final video at or below five minutes.
- Upload publicly to YouTube or Vimeo.
- Add the public video URL to Devpost.

The existing script may begin checked. Recording, duration verification, upload, and Devpost linking begin unchecked.

### Bonus articles

- Draft Article 1.
- Draft Article 2.
- Draft Article 3.
- Fact-check all three drafts.
- Select privacy-safe screenshots.
- Publish all three publicly on AWS Builder.
- Verify all URLs while signed out.
- Add all three URLs to Devpost.

Drafting and fact-checking begin checked. Screenshot selection, publication, URL verification, and Devpost linking begin unchecked.

## Article Library

The page embeds the exact Markdown content of:

- `docs/builder-articles/01-why-i-built-contactloop.md`
- `docs/builder-articles/02-building-contactloop.md`
- `docs/builder-articles/03-ai-and-teacher-judgment.md`

Each article is rendered as readable HTML inside a native `<details>` element. The summary row shows the article number, title, word count, and draft status. Opening one article does not force the others closed.

Controls above the article library provide:

- expand all;
- collapse all;
- copy an individual article as plain text.

Copy feedback appears inline and does not use a blocking alert. If the Clipboard API is unavailable, the page uses a temporary text area fallback.

## Visual Direction

The visual direction is an editorial submission desk rather than a generic dashboard.

- Background: warm paper tone with subtle grid and grain created in CSS.
- Primary ink: deep forest green.
- Completion accent: sharp chartreuse.
- Pending accent: restrained amber.
- Display typography: Georgia for editorial character.
- Interface and metadata typography: Trebuchet MS and monospace fallbacks.
- Components: crisp paper cards, offset borders, tab-like group labels, and restrained shadows.
- Motion: short entry reveal and accordion indicator rotation, disabled under `prefers-reduced-motion`.

The page must remain readable at narrow mobile widths. Checklist rows stack their evidence notes beneath the main label, and article typography uses a comfortable line length.

## Accessibility

- Use semantic headings, sections, native checkboxes, buttons, and `<details>` elements.
- Associate every checkbox with a visible label.
- Preserve visible keyboard focus.
- Do not encode status by color alone; include text labels and counts.
- Respect `prefers-reduced-motion`.
- Maintain readable contrast for body text, pending status, and completed status.

## Data and Error Handling

- No private data is embedded.
- The HTML contains demo/project content only.
- Malformed or outdated saved checkbox state falls back to evidence-based defaults.
- Local storage failures do not prevent checkbox interaction during the current session.
- Copy failures show an inline message telling the user to select the article manually.
- The reset action requires confirmation because it overwrites saved progress.

## Verification

- Open the standalone HTML directly and through the Vite/public path.
- Confirm initial checked states match available evidence.
- Change a pending item, reload, and confirm persistence.
- Reset and confirm evidence-based defaults return.
- Expand and collapse each article.
- Use expand-all and collapse-all controls.
- Copy each article and confirm complete text is copied.
- Verify the completion percentage and count update correctly.
- Test at desktop and mobile viewport widths.
- Run an HTML/source contract test for required sections, local-storage key, article titles, and article text.
- Run the full project test suite and production build.

## Acceptance Criteria

- One HTML page contains the complete final delivery checklist and all three full articles.
- Articles are independently collapsible and can be copied.
- Checklist changes persist locally and can be reset.
- Only verified items begin checked.
- Pending external actions remain visibly incomplete.
- Progress accurately reflects current checkbox state.
- The page works without network access or a framework.
- The page is responsive, keyboard accessible, and visually consistent with ContactLoop.
- `docs/` and `public/` copies are identical.
