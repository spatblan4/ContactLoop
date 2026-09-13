import test from 'node:test';
import assert from 'node:assert/strict';
import { toastMarkup } from '../src/lib/toast.js';

test('toast markup renders a success message', () => {
  assert.match(toastMarkup({ message: 'Student added', tone: 'success' }), /Student added/);
  assert.match(toastMarkup({ message: 'Student added', tone: 'success' }), /app-toast/);
});
