# Demo and Beta Telephony Design

## Goal

Keep the hackathon demo safe and clearly simulated while making the Beta deployment use the real Twilio call path.

## Behavior

- Demo mode keeps the manual outcome workflow and labels it as a simulation.
- Demo outcome choices do not claim a fabricated call duration.
- Beta mode sets `VITE_TELEPHONY_PROVIDER=twilio`; clicking Call now invokes the existing Supabase `start-call` Edge Function instead of opening the manual outcome picker.
- No phone call is initiated during automated verification.

## Boundaries

- Reuse the existing `MockTelephonyProvider` and `TwilioTelephonyProvider`.
- Do not change Supabase data tables or Twilio credentials.
- Verify configuration, tests, and both build modes before deployment.

## Acceptance

- Demo shows “Demo simulation” and no `7m 43s` in the call workflow.
- Beta build resolves the telephony provider to `twilio`.
- Existing automated tests and both Vite builds pass.
