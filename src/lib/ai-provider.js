export class ContactBriefProvider {
  async generate() {
    throw new Error('Contact brief provider is not configured.');
  }
}

export class AwsStrandsContactBriefProvider extends ContactBriefProvider {
  constructor({ endpoint, fetchImpl, invokeImpl } = {}) {
    super();
    this.endpoint = endpoint;
    this.fetchImpl = fetchImpl ?? globalThis.fetch?.bind(globalThis);
    this.invokeImpl = invokeImpl;
  }

  async generate({ studentId, dateFrom, dateTo, includeNotes = true }) {
    const body = { student_id: studentId, date_from: dateFrom, date_to: dateTo, include_notes: includeNotes };
    if (this.invokeImpl) return this.invokeImpl(body);
    if (!this.endpoint) throw new Error('AWS Contact Brief endpoint is not configured.');
    const response = await this.fetchImpl(`${this.endpoint.replace(/\/$/, '')}/contact-brief`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (!response.ok) {
      let detail = '';
      try {
        const payload = await response.clone().json();
        detail = typeof payload?.error === 'string' ? payload.error : '';
      } catch {
        // Keep the status-only message when the backend did not return JSON.
      }
      throw new Error(`AWS Contact Brief provider failed (${response.status})${detail ? `: ${detail}` : '.'}`);
    }
    return response.json();
  }
}

export function createContactBriefProvider({ provider = 'none', endpoint, fetchImpl, invokeImpl } = {}) {
  if (provider === 'aws-strands-bedrock') return new AwsStrandsContactBriefProvider({ endpoint, fetchImpl, invokeImpl });
  return new ContactBriefProvider();
}
