import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const appSource = readFileSync(new URL('../src/app.js', import.meta.url), 'utf8');

test('login brand provides a home navigation target', () => {
  assert.match(appSource, /<button class="auth-brand" data-home type="button" aria-label="Return to home">/);
});

test('restored email-link sessions open the dashboard instead of remaining on home', () => {
  assert.match(appSource, /const session=await getAuthSession\(\);state\.auth=\{\.\.\.state\.auth,status:session\?'authenticated':'signed-out',session,error:null\};if\(session\)state\.screen='dashboard';render\(\);/);
});

test('email-link sign-in events open the dashboard', () => {
  assert.match(appSource, /subscribeToAuthChanges\(\(event,session\)=>\{state\.auth=.*?if\(session\)\{if\(event==='SIGNED_IN'\)state\.screen='dashboard';/);
});

test('pre-call topic dialog can be closed', () => {
  assert.match(appSource, /function renderPlannedTopicModal\(\).*?document\.querySelectorAll\('\[data-close\]'\)\.forEach\(button=>button\.onclick=/);
});
