export function googleOperationPath(jobId: string) {
  if (/^\d+$/.test(jobId)) return `operations/${jobId}`;
  if (/^operations\/\d+$/.test(jobId)) return jobId;
  throw new Error('Invalid Google transcription operation.');
}
