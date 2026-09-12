const DEMO_OUTREACH_COPY = [
  ['high', 'A follow-up is due and the last contact did not connect.', 'Call today to confirm a new time to talk.'],
  ['medium', 'The family has not had a recent successful contact.', 'Review the contact history before reaching out.'],
  ['low', 'A teacher-confirmed note suggests a quick check-in would help.', 'Send a brief check-in and offer a call.'],
];
const DEMO_OUTREACH_NAMES = ['Emma Johnson', 'Ava Chen', 'Noah Williams'];

export function demoOutreachName(index) {
  return DEMO_OUTREACH_NAMES[index];
}

export function createDemoOutreachPlan(students = []) {
  return {
    generatedAt: null,
    source: 'demo',
    items: DEMO_OUTREACH_COPY.map(([priority, reason, suggestedNextStep], index) => ({
      studentId: students[index]?.id || `demo-outreach-${index + 1}`,
      priority,
      reason,
      suggestedNextStep,
    })),
  };
}
