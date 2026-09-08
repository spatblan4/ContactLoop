# ContactLoop

**A teacher-first communication workspace that turns repeated family outreach into a reliable loop of contact, follow-up, context, and human-reviewed AI preparation.**

ContactLoop is an entry for the [AWS Agents for Humans Hackathon](https://agentsforhumans.devpost.com/), aligned with the Good Neighbor Agents track.

## What ContactLoop does

Teachers can organize students and guardians, start a phone call, preserve the call result, distinguish planned topics from topics actually discussed, and keep unsuccessful outreach visible as an open follow-up. ContactLoop then uses a narrowly scoped agent to prepare a structured Contact Brief from contact statistics, teacher notes, and unresolved follow-ups.

Every generated brief starts in `pending` review status. A teacher can edit, review, and approve it before it becomes part of the final meeting record. AI prepares the record; the teacher remains accountable for it.

## Architecture

ContactLoop uses a Vite single-page application with two runtime modes:

- **Demo:** a login-free hackathon experience using controlled demo data.
- **Authenticated Beta:** a private teacher workspace with Supabase Auth and roster import.

The application combines:

- **AWS Strands Agents SDK + Amazon Bedrock:** generate Contact Briefs through three narrow tools: contact statistics, teacher notes/topics, and open follow-ups.
- **AWS Lambda-compatible Python provider:** runs the agent and returns structured JSON with `review_status: "pending"`.
- **Supabase:** stores student, guardian, contact-event, follow-up, note, and brief data; Edge Functions protect server-only integrations.
- **Twilio:** starts outbound calls and reports provider status back to the contact record.
- **Google Cloud Speech-to-Text:** optionally transcribes separate teacher-recorded voice notes. It is not part of guardian calls.

See [the AWS provider guide](ai/README.md), [trial setup](docs/trial-setup.md), and [architecture diagram](docs/architecture.html) for deeper implementation detail.

## Local development

Requirements: Node.js 20 or later and npm.

```bash
git clone https://github.com/spatblan4/ContactLoop.git
cd ContactLoop
npm install
cp .env.example .env.demo.local
npm run dev:demo
```

Set a demo Supabase project URL and anonymous key in `.env.demo.local` before opening the app. For an authenticated workspace, create `.env.beta.local`, set `VITE_APP_MODE=authenticated`, follow [the Beta setup guide](docs/trial-setup.md), and run `npm run dev:beta`.

The base database definition is in `supabase/schema.sql`. Feature patches in `supabase/` document the incremental schema used by the current build. The AI flow additionally requires `supabase/patch-ai-contact-brief.sql` and a deployed provider as described in `ai/README.md`.

## Environment variables

Browser-safe Vite configuration:

```text
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
VITE_APP_MODE=demo
VITE_TELEPHONY_PROVIDER=mock
VITE_CONTACT_BRIEF_PROVIDER=none
VITE_AWS_CONTACT_BRIEF_ENDPOINT=
```

Production integrations also require server-side secrets for Supabase service access, Twilio, AWS/Bedrock, and optional teacher voice-note transcription. Never prefix secrets with `VITE_` or commit local `.env` files. Exact server-side names and deployment boundaries are documented in `ai/README.md`, `docs/trial-setup.md`, and the relevant `supabase/functions/` source.

## Testing

```bash
npm test
npm run build
```

The Node test suite covers contact event ordering, follow-ups, student actions, provider boundaries, Twilio status/signature handling, voice-note behavior, and the submission artifacts.

## Privacy and safety boundaries

- ContactLoop does not record or transcribe guardian calls.
- Optional voice transcription applies only to a separate note intentionally recorded by the teacher.
- Public demos and screenshots must use synthetic data, never real student or guardian information.
- Supabase service-role, Twilio, Google Cloud, and AWS credentials stay in server-side environments.
- Agent tools are read-only and narrowly scoped; authoritative counts come from a database RPC rather than model inference.
- AI output remains pending until a teacher reviews and approves it.

The latest repository privacy check is recorded in [docs/submission/privacy-scan.md](docs/submission/privacy-scan.md).

## Hackathon development disclosure

### Before the hackathon

The underlying problem insight came from observing how easily repeated teacher-family outreach becomes fragmented across calls, notes, and memory. ContactLoop existed as a product concept and workflow direction before implementation began.

### Built during Agents for Humans

The first verifiable repository snapshot is dated **August 26, 2026**. The current application implementation, contact workflow, demo/Beta modes, Twilio integration, follow-up logic, teacher notes, AWS Strands/Bedrock Contact Brief provider, human review flow, tests, architecture material, submission center, and article drafts are represented in commits from August 26, 2026 onward.

This disclosure distinguishes prior problem discovery and concept work from the code and submission artifacts evidenced in this repository.

## License

[MIT](LICENSE)
