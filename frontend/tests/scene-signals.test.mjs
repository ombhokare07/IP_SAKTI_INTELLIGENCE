import test from 'node:test';
import assert from 'node:assert/strict';
import {
  createSceneTransitionState,
  normalizeJurisdictions,
  normalizeProviderTone,
  normalizeRiskTone,
  normalizeSceneCount,
  normalizeSceneScore,
  reduceSceneTransition,
  WORKSPACE_ROUTE_ORDER,
} from '../src/services/scene-signals.mjs';

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

test('scene transition direction follows workspace navigation order', () => {
  const dashboard = createSceneTransitionState('dashboard');
  const forward = reduceSceneTransition(dashboard, 'prior-art', 100);
  const confirmed = reduceSceneTransition(forward, 'prior-art', 110, true);
  const backward = reduceSceneTransition(confirmed, 'ask', 120);
  assert.equal(forward.direction, 1);
  assert.equal(backward.direction, -1);
  assert.ok(WORKSPACE_ROUTE_ORDER.indexOf('regulatory-alerts') < WORKSPACE_ROUTE_ORDER.indexOf('knowledge-library'));
  const alerts = createSceneTransitionState('regulatory-alerts');
  assert.equal(reduceSceneTransition(alerts, 'knowledge-library', 130).direction, 1);
  const library = createSceneTransitionState('knowledge-library');
  assert.equal(reduceSceneTransition(library, 'regulatory-alerts', 140).direction, -1);
});

test('first route confirmation primes the scene without inventing a departure', () => {
  const empty = createSceneTransitionState();
  const primed = reduceSceneTransition(empty, 'prior-art', 100, true);
  assert.deepEqual(primed, {
    route: 'prior-art', fromRoute: 'prior-art', toRoute: 'prior-art',
    transitionStartedAt: 0, direction: 0, transitionRevision: 0,
  });
});

test('same-route departures are a stable no-op', () => {
  const dashboard = createSceneTransitionState('dashboard');
  assert.equal(reduceSceneTransition(dashboard, '/dashboard?tab=recent', 100), dashboard);
});

test('rapid retargeting overwrites the destination without a queue', () => {
  const dashboard = createSceneTransitionState('dashboard');
  const patentability = reduceSceneTransition(dashboard, 'patentability', 100);
  const priorArt = reduceSceneTransition(patentability, 'prior-art', 112);
  const stalePatentabilityConfirmation = reduceSceneTransition(priorArt, 'patentability', 118, true);
  const confirmedPriorArt = reduceSceneTransition(stalePatentabilityConfirmation, 'prior-art', 120, true);
  assert.equal(priorArt.fromRoute, 'dashboard');
  assert.equal(priorArt.toRoute, 'prior-art');
  assert.equal(priorArt.transitionStartedAt, 112);
  assert.equal(priorArt.transitionRevision, 2);
  assert.equal(stalePatentabilityConfirmation, priorArt);
  assert.equal(confirmedPriorArt.route, 'prior-art');
});
