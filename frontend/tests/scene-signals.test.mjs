import test from 'node:test';
import assert from 'node:assert/strict';
import { normalizeJurisdictions, normalizeProviderTone, normalizeRiskTone, normalizeSceneCount, normalizeSceneScore } from '../src/services/scene-signals.mjs';

test('scene counts remain missing when input is absent or invalid', () => {
  assert.equal(normalizeSceneCount(undefined), undefined);
  assert.equal(normalizeSceneCount(null), undefined);
  assert.equal(normalizeSceneCount(-1), undefined);
  assert.equal(normalizeSceneCount('unknown'), undefined);
});

test('scene counts are integers and stay within their explicit cap', () => {
  assert.equal(normalizeSceneCount(7.9), 7);
  assert.equal(normalizeSceneCount('120', 15), 15);
});

test('scene scores accept ratios or percentages without inventing missing values', () => {
  assert.equal(normalizeSceneScore(undefined), undefined);
  assert.equal(normalizeSceneScore(0.72), 0.72);
  assert.equal(normalizeSceneScore(72), 0.72);
  assert.equal(normalizeSceneScore(180), 1);
});

test('scene jurisdictions are normalized, unique and bounded', () => {
  assert.deepEqual(normalizeJurisdictions(['in', 'US', 'in', ' eu ', 'uk', 'ca']), ['IN', 'US', 'EU', 'UK']);
  assert.deepEqual(normalizeJurisdictions(undefined), []);
  assert.equal(normalizeProviderTone('connected'), 'neutral');
  assert.equal(normalizeProviderTone('ready'), 'ready');
  assert.equal(normalizeRiskTone('high'), 'high');
  assert.equal(normalizeRiskTone('insufficient_evidence'), undefined);
});
