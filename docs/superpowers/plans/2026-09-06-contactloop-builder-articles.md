# ContactLoop AWS Builder Articles Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce three publication-ready English AWS Builder articles about ContactLoop's origin, Strands/AWS implementation, and human-in-the-loop design.

**Architecture:** Create one focused Markdown draft per article plus a shared evidence matrix. Draft each article against repository evidence, then run a cross-article editorial pass to remove repetition, unsupported claims, private implementation details, and inconsistent terminology.

**Tech Stack:** Markdown, repository source and documentation, Strands Agents SDK, Amazon Bedrock, Twilio, Supabase, AWS Builder.

## Global Constraints

- Every article title must contain the exact phrase `Agents for Humans`.
- Article 1 must remain a restrained founder story and must not disclose the complete product blueprint.
- Do not publish credentials, service-role keys, full prompts, complete tool payloads, sensitive test data, internal business rules, commercial strategy, or unreleased roadmap.
- Do not claim measured time savings or formal FERPA, COPPA, GDPR, or other regulatory compliance.
- Do not imply that ContactLoop records, transcribes, or automatically understands parent phone conversations.
- Describe planned topics separately from teacher-confirmed discussed topics.
- Describe AI output as pending teacher review until a teacher edits or approves it.
- All screenshots selected later must use demo data and contain no real student, guardian, phone, credential, or service information.
- The target publication date is September 13, 2026.

---

## File Structure

- Create `docs/builder-articles/evidence-matrix.md`: shared source-of-truth for claims, terminology, and disclosure limits.
- Create `docs/builder-articles/01-why-i-built-contactloop.md`: 700–900 word origin and problem article.
- Create `docs/builder-articles/02-building-contactloop.md`: 1,100–1,400 word technical implementation article.
- Create `docs/builder-articles/03-ai-and-teacher-judgment.md`: 800–1,000 word trust and human judgment article.

### Task 1: Build the Evidence Matrix

**Files:**
- Create: `docs/builder-articles/evidence-matrix.md`
- Read: `README.md`
- Read: `ai/README.md`
- Read: `ai/contact_brief/tools.py`
- Read: `ai/contact_brief/handler.py`
- Read: `src/lib/telephony.js`
- Read: `src/lib/ai-provider.js`
- Read: `src/lib/contact-events.js`
- Read: `src/lib/followup-items.js`
- Read: `docs/ContactLoop Devpost Video Script — Condensed.md`

**Interfaces:**
- Consumes: current repository behavior and the user's confirmation that real Twilio calling and result write-back work end to end.
- Produces: a Markdown table with columns `Claim`, `Evidence`, `Allowed wording`, `Prohibited wording`, and `Articles`.

- [ ] **Step 1: Record verified product claims**

Create a table covering real test-phone calling, call-status write-back, student/guardian association, planned versus discussed topics, open follow-ups, Strands tools, Bedrock generation, authoritative Supabase counts, pending review, teacher editing/approval, and the no-recording/no-call-transcription boundary.

- [ ] **Step 2: Record consistent terminology**

Use these exact product terms consistently: `ContactLoop`, `Contact Brief`, `Needs Teacher Review`, `Teacher Approved`, `planned topic`, `discussed topics`, and `open follow-up`.

- [ ] **Step 3: Verify every claim against evidence**

Run:

```bash
rg -n "Strands|Bedrock|review_status|get_contact_stats|get_teacher_notes_and_topics|get_open_follow_ups|Twilio|planned_topic|discussed_topics" ai src docs
```

Expected: each allowed technical claim maps to at least one repository location or the user's explicit live-flow confirmation.

- [ ] **Step 4: Commit the evidence matrix**

```bash
git add docs/builder-articles/evidence-matrix.md
git commit -m "docs: add ContactLoop article evidence matrix"
```

### Task 2: Draft the Origin Story

**Files:**
- Create: `docs/builder-articles/01-why-i-built-contactloop.md`
- Read: `docs/builder-articles/evidence-matrix.md`
- Read: `docs/ContactLoop Devpost Video Script — Condensed.md`

**Interfaces:**
- Consumes: verified founder story and high-level outcome claims from the evidence matrix.
- Produces: a 700–900 word publication-ready English article with the title `Agents for Humans: Why I Built ContactLoop for the Conversations Teachers Can't Afford to Lose`.

- [ ] **Step 1: Write the opening scene**

Open with the conversation about a fellow teacher arriving home almost two hours later and the realization that documentation, not traffic, was the cause.

- [ ] **Step 2: Develop the problem without revealing the blueprint**

Explain the continuity problem across attempted calls, discussed topics, and unresolved follow-ups. Keep implementation at outcome level and omit component names, prompts, tool schemas, and future plans.

- [ ] **Step 3: State ContactLoop's promise and human purpose**

Describe ContactLoop as protecting the continuity of family communication. Close with the principle that AI handles remembering and organizing so teachers can focus on relationships.

- [ ] **Step 4: Check length and restricted disclosures**

Run:

```bash
wc -w docs/builder-articles/01-why-i-built-contactloop.md
rg -ni "system prompt|service.role|roadmap|pricing|FERPA|COPPA|GDPR|records calls|transcribes calls" docs/builder-articles/01-why-i-built-contactloop.md
```

Expected: word count is 700–900; restricted-disclosure search returns no unsupported claims.

- [ ] **Step 5: Commit Article 1**

```bash
git add docs/builder-articles/01-why-i-built-contactloop.md
git commit -m "docs: draft ContactLoop origin article"
```

### Task 3: Draft the Technical Build Article

**Files:**
- Create: `docs/builder-articles/02-building-contactloop.md`
- Read: `docs/builder-articles/evidence-matrix.md`
- Read: `ai/README.md`
- Read: `ai/contact_brief/tools.py`
- Read: `ai/contact_brief/handler.py`
- Read: `src/lib/telephony.js`
- Read: `src/lib/ai-provider.js`

**Interfaces:**
- Consumes: component responsibilities and verified claims from the evidence matrix.
- Produces: a 1,100–1,400 word publication-ready English article with the title `Agents for Humans: Building ContactLoop with Strands Agents, Amazon Bedrock, Twilio, and Supabase`.

- [ ] **Step 1: Explain why the problem requires an agent workflow**

Contrast persistent, tool-using work with a general chat response. Define the desired flow as retrieving facts, organizing context, and preparing a reviewable brief.

- [ ] **Step 2: Explain the event and data layer**

Describe real Twilio calling and status return, then explain Supabase as the source for contact events, outcomes, duration, teacher-confirmed context, and follow-up state.

- [ ] **Step 3: Explain the Strands and Bedrock layer**

Describe the three narrow tool responsibilities and how Bedrock converts verified tool output into a contextual Contact Brief. State that numerical facts come from authoritative queries rather than model inference.

- [ ] **Step 4: Explain teacher review and implementation lessons**

Describe pending review, editing, approval, and the lessons of narrow tools, fact/narrative separation, and explicit human authority.

- [ ] **Step 5: Add a text architecture flow**

Include this publication-safe flow without credentials or payload schemas:

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

- [ ] **Step 6: Check length, AWS naming, and restricted disclosures**

Run:

```bash
wc -w docs/builder-articles/02-building-contactloop.md
rg -n "Strands Agents|Amazon Bedrock|Twilio|Supabase|Needs Teacher Review" docs/builder-articles/02-building-contactloop.md
rg -ni "service.role.key|SUPABASE_SERVICE_ROLE_KEY|secret|full prompt|FERPA|COPPA|GDPR" docs/builder-articles/02-building-contactloop.md
```

Expected: word count is 1,100–1,400; all named components and review state appear; no credential, full-prompt, or unsupported compliance disclosure appears.

- [ ] **Step 7: Commit Article 2**

```bash
git add docs/builder-articles/02-building-contactloop.md
git commit -m "docs: draft ContactLoop technical article"
```

### Task 4: Draft the Trust and Judgment Article

**Files:**
- Create: `docs/builder-articles/03-ai-and-teacher-judgment.md`
- Read: `docs/builder-articles/evidence-matrix.md`
- Read: `ai/README.md`
- Read: `docs/ContactLoop Devpost Video Script — Condensed.md`

**Interfaces:**
- Consumes: verified review states, product boundaries, and planned-versus-discussed distinction.
- Produces: an 800–1,000 word publication-ready English article with the title `Agents for Humans: AI Should Prepare the Record, Not Replace the Teacher's Judgment`.

- [ ] **Step 1: Establish the risk of assumed context**

Explain that family communication is high-context and that software must not convert planned intent or a missed attempt into a claim about what happened.

- [ ] **Step 2: Explain the fact and interpretation boundary**

Describe database-backed facts separately from model-generated narrative, including teacher-confirmed discussed topics and open follow-ups.

- [ ] **Step 3: Explain review and product boundaries**

Describe `Needs Teacher Review`, editing, and `Teacher Approved`. State that ContactLoop does not record parent calls or automatically transcribe family conversations.

- [ ] **Step 4: End with three reusable design lessons**

Use these lessons: keep tools narrow, make uncertainty visible, and preserve a clear human decision point.

- [ ] **Step 5: Check length and safety language**

Run:

```bash
wc -w docs/builder-articles/03-ai-and-teacher-judgment.md
rg -n "planned topic|discussed topics|Needs Teacher Review|Teacher Approved|does not record|does not automatically transcribe" docs/builder-articles/03-ai-and-teacher-judgment.md
rg -ni "guaranteed|error.free|fully compliant|FERPA compliant|COPPA compliant|GDPR compliant" docs/builder-articles/03-ai-and-teacher-judgment.md
```

Expected: word count is 800–1,000; all required distinctions and boundaries appear; no guarantee or unsupported compliance claim appears.

- [ ] **Step 6: Commit Article 3**

```bash
git add docs/builder-articles/03-ai-and-teacher-judgment.md
git commit -m "docs: draft ContactLoop trust article"
```

### Task 5: Cross-Series Editorial and Publication QA

**Files:**
- Modify: `docs/builder-articles/01-why-i-built-contactloop.md`
- Modify: `docs/builder-articles/02-building-contactloop.md`
- Modify: `docs/builder-articles/03-ai-and-teacher-judgment.md`
- Read: `docs/builder-articles/evidence-matrix.md`

**Interfaces:**
- Consumes: three complete article drafts and the shared evidence matrix.
- Produces: a coherent, non-repetitive, fact-checked series ready for the user's final review and publication.

- [ ] **Step 1: Verify titles and terminology**

Run:

```bash
rg -L "^# Agents for Humans" docs/builder-articles/0*.md
rg -n "Contact Loop|Contact loop|contactloop|contact brief|needs teacher review|teacher approved" docs/builder-articles/0*.md
```

Expected: the first command returns no filenames; terminology review results are corrected to the approved product terms where applicable.

- [ ] **Step 2: Remove repeated openings and explanations**

Keep the colleague story in Article 1, the complete architecture explanation in Article 2, and the planned-versus-discussed ethical analysis in Article 3. Other articles may reference those ideas in one sentence but must not retell them.

- [ ] **Step 3: Verify claims against the evidence matrix**

Review every sentence containing a capability, AWS component, data flow, or product boundary. Remove or qualify any sentence that is not supported by the evidence matrix.

- [ ] **Step 4: Run final disclosure and formatting checks**

Run:

```bash
rg -ni "API[_ -]?key|password|token|service.role|secret|real student|real guardian|roadmap|pricing|FERPA compliant|COPPA compliant|GDPR compliant" docs/builder-articles/0*.md
git diff --check -- docs/builder-articles
wc -w docs/builder-articles/0*.md
```

Expected: no secrets, private data, roadmap, pricing, or unsupported compliance claims; no whitespace errors; each article remains within its target range.

- [ ] **Step 5: Commit the editorial pass**

```bash
git add docs/builder-articles/01-why-i-built-contactloop.md docs/builder-articles/02-building-contactloop.md docs/builder-articles/03-ai-and-teacher-judgment.md
git commit -m "docs: polish ContactLoop builder article series"
```

- [ ] **Step 6: Hand off for publication**

Provide the user with links to all three local Markdown drafts and a short publication checklist: paste into AWS Builder, add verified demo screenshots, preview formatting, publish publicly on September 13, verify each URL in a signed-out browser, and add all three URLs to Devpost before September 14 at 5:00 PM PDT.
