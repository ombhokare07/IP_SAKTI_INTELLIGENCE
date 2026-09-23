import assert from 'node:assert/strict';
import test from 'node:test';

import {
  authSessionStatus,
  countConnectedProviders,
  describeStatus,
  summarizeProviders,
} from '../src/services/status.mjs';

test('configured, synthetic and authorization-required providers are not counted as connected', () => {
  const providers = {
    verified: 'ready',
    local: 'local',
    configured: 'configured',
    unverified: 'configured_not_verified',
    synthetic: 'mock',
    gated: 'authorization_required',
  };
  assert.equal(countConnectedProviders(providers), 2);
  assert.deepEqual(summarizeProviders(providers), {
    connected: 2,
    total: 6,
    label: '2 verified / connected',
    tone: 'positive',
  });
});

test('truthful provider labels keep materially different states distinct', () => {
  assert.equal(describeStatus('local').label, 'Local');
  assert.equal(describeStatus('configured_not_verified').label, 'Configured · not verified');
  assert.equal(describeStatus('authorization_required').label, 'Authorization required');
  assert.equal(describeStatus('mock').label, 'Synthetic test data');
  assert.equal(describeStatus('not connected').label, 'Not connected');
});

test('normal-user authentication is derived from Google and session-cookie configuration', () => {
  const configured = authSessionStatus({authentication: {google_sign_in: 'configured', session_cookie: 'configured'}});
  assert.equal(configured.connected, true);
  assert.equal(describeStatus(configured).label, 'Google session configured');
  assert.equal(authSessionStatus({authentication_required: false, authentication: {google_sign_in: 'not_configured', session_cookie: 'not_configured'}}).connected, false);
});
