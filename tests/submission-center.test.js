import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';

const docsPath = new URL('../docs/contactloop-submission-center.html', import.meta.url);
const publicPath = new URL('../public/contactloop-submission-center.html', import.meta.url);

test('submission center includes the complete persistent checklist contract', async () => {
  const html = await readFile(docsPath, 'utf8');

  assert.match(html, /contactloop-submission-center-v2/);
  for (const group of ['accounts', 'product', 'technical', 'repository', 'devpost', 'video', 'articles']) {
    assert.match(html, new RegExp(`data-check-group="${group}"`));
  }
  assert.match(html, /data-check-id="product-real-call"[^>]*checked/);
  for (const id of ['tech-setup', 'repo-readme', 'repo-license', 'repo-disclosure', 'repo-privacy', 'devpost-description', 'devpost-pitch']) {
    assert.match(html, new RegExp(`data-check-id="${id}"[^>]*checked`));
  }
  assert.match(html, /data-check-id="devpost-submit"[^>]*type="checkbox">/);
  assert.match(html, /id="progressPercent"/);
  assert.match(html, /id="progressCount"/);
  assert.match(html, /id="resetProgress"/);
  assert.match(html, /data-default-checked/);
  assert.equal((html.match(/data-default-checked="true"/g) || []).length, 26);
  assert.equal((html.match(/data-check-id=/g) || []).length, 54);
});

test('submission center embeds three accessible collapsible articles and controls', async () => {
  const html = await readFile(docsPath, 'utf8');

  assert.equal((html.match(/<details class="article-card"/g) || []).length, 3);
  assert.match(html, /Agents for Humans: Why I Built ContactLoop/);
  assert.match(html, /Agents for Humans: Building ContactLoop/);
  assert.match(html, /Agents for Humans: AI Should Prepare the Record/);
  assert.match(html, /id="expandAll"/);
  assert.match(html, /id="collapseAll"/);
  assert.equal((html.match(/data-copy-source=/g) || []).length, 3);
  assert.match(html, /navigator\.clipboard/);
  assert.match(html, /document\.execCommand\('copy'\)/);
  assert.match(html, /prefers-reduced-motion/);
});

test('public submission center is identical to the docs source', async () => {
  const [html, publicHtml] = await Promise.all([
    readFile(docsPath, 'utf8'),
    readFile(publicPath, 'utf8'),
  ]);

  assert.equal(publicHtml, html);
});

test('submission center binds reset without colliding with the button id global', async () => {
  const html = await readFile(docsPath, 'utf8');

  assert.doesNotMatch(html, /function resetProgress\(/);
  assert.match(html, /document\.querySelector\('#resetProgress'\)\.addEventListener/);
});

test('submission center provides an inline favicon for clean offline loading', async () => {
  const html = await readFile(docsPath, 'utf8');

  assert.match(html, /<link rel="icon" href="data:image\/svg\+xml,/);
});
