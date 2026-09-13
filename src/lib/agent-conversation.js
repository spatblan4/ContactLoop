// Conversation state shared by the outreach QA box and the Teacher
// Assistant modal. Messages are {role: 'teacher' | 'agent', text} pairs.

export function createConversationState() {
  return { messages: [], input: '', loading: false, error: null };
}

export function normalizeConversationMessages(payload) {
  const messages = Array.isArray(payload?.messages) ? payload.messages : [];
  return messages
    .map(message => ({
      role: message?.role === 'user' ? 'teacher' : 'agent',
      text: String(message?.text || '').trim(),
    }))
    .filter(message => message.text);
}

export function messageSubmitted(state, text) {
  const question = String(text || '').trim();
  return {
    ...state,
    messages: [...state.messages, { role: 'teacher', text: question }],
    input: '',
    loading: true,
    error: null,
  };
}

export function answerReceived(state, answer) {
  return {
    ...state,
    loading: false,
    error: null,
    messages: [...state.messages, { role: 'agent', text: String(answer || '').trim() }],
  };
}

export function conversationFailed(state, message) {
  return {
    ...state,
    loading: false,
    error: message || 'The assistant is temporarily unavailable. Try again shortly.',
  };
}
