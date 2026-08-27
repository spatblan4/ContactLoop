import { googleOperationPath } from './google-operation.ts';

function assertEquals(actual: unknown, expected: unknown) {
  if (actual !== expected) throw new Error(`Expected ${expected}, received ${actual}`);
}

function assertThrows(callback: () => unknown, expectedMessage: string) {
  try {
    callback();
  } catch (error) {
    if (error instanceof Error && error.message.includes(expectedMessage)) return;
    throw error;
  }
  throw new Error(`Expected error containing: ${expectedMessage}`);
}

Deno.test('normalizes the numeric operation id returned by Speech-to-Text V1', () => {
  assertEquals(
    googleOperationPath('2361840430624526419'),
    'operations/2361840430624526419',
  );
});

Deno.test('accepts an already normalized Speech-to-Text operation path', () => {
  assertEquals(
    googleOperationPath('operations/2361840430624526419'),
    'operations/2361840430624526419',
  );
});

Deno.test('rejects operation ids from unrelated providers', () => {
  assertThrows(
    () => googleOperationPath('contactloop-student-123'),
    'Invalid Google transcription operation.',
  );
});
