export function buildGcsResumableUploadRequest({ bucket, objectKey, contentType }) {
  return {
    url: `https://storage.googleapis.com/upload/storage/v1/b/${encodeURIComponent(bucket)}/o?uploadType=resumable&name=${encodeURIComponent(objectKey)}`,
    headers: { 'Content-Type': 'application/json', 'X-Upload-Content-Type': contentType },
    body: {},
  };
}

export function buildSpeechRecognitionRequest({ gcsUri }) {
  return {
    config: { encoding: 'WEBM_OPUS', languageCode: 'en-US', model: 'latest_long' },
    audio: { uri: gcsUri },
  };
}
