import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';

const read = path => readFile(new URL(`../${path}`, import.meta.url), 'utf8');

test('README explains the project, setup, safety boundaries, and hackathon work', async () => {
  const readme = await read('README.md');

  for (const heading of [
    '## What ContactLoop does',
    '## Architecture',
    '## Local development',
    '## Environment variables',
    '## Testing',
    '## Privacy and safety boundaries',
    '## Hackathon development disclosure',
    '### Before the hackathon',
    '### Built during Agents for Humans',
  ]) assert.match(readme, new RegExp(heading.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')));

  assert.match(readme, /npm run dev:demo/);
  assert.match(readme, /npm test/);
  assert.match(readme, /npm run build/);
  assert.match(readme, /August 26, 2026/);
  assert.match(readme, /does not record or transcribe guardian calls/i);
});

test('repository includes an MIT license', async () => {
  const license = await read('LICENSE');

  assert.match(license, /^MIT License/);
  assert.match(license, /Copyright \(c\) 2026 ContactLoop contributors/);
  assert.match(license, /Permission is hereby granted, free of charge/);
});

test('Devpost draft contains the standard narrative fields and consistent pitch', async () => {
  const draft = await read('docs/devpost-submission.md');

  assert.match(draft, /# ContactLoop/);
  assert.match(draft, /A teacher-first communication workspace/);
  for (const heading of ['Inspiration', 'What it does', 'How we built it', 'Challenges we ran into', 'Accomplishments that we\'re proud of', 'What we learned', 'What\'s next for ContactLoop']) {
    assert.match(draft, new RegExp(`## ${heading}`));
  }
  assert.match(draft, /Strands Agents SDK/);
  assert.match(draft, /Amazon Bedrock/);
  assert.match(draft, /human-in-the-loop/);
});

test('privacy scan records scope, safe results, and limitations', async () => {
  const report = await read('docs/submission/privacy-scan.md');

  assert.match(report, /Scan date: 2026-09-08/);
  assert.match(report, /No tracked environment files were found/);
  assert.match(report, /No high-confidence credential values were found/);
  assert.match(report, /filename-only/i);
  assert.match(report, /does not replace/i);
});
