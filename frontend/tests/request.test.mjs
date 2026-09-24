import assert from 'node:assert/strict';
import test from 'node:test';

import { buildApiHeaders } from '../src/services/request.mjs';

test('bodyless GET headers omit JSON content type and preserve authentication', () => {
  assert.deepEqual(buildApiHeaders({}, false), {});
  assert.deepEqual(buildApiHeaders({ Authorization: 'Bearer test-token' }, false), {
    Authorization: 'Bearer test-token',
  });
});

test('JSON request headers include content type and preserve authentication', () => {
  assert.deepEqual(buildApiHeaders({ Authorization: 'Bearer test-token' }, true), {
    'Content-Type': 'application/json',
    Authorization: 'Bearer test-token',
  });
});
