export const SCENE_PHASES = ['idle', 'input', 'submitting', 'processing', 'success', 'partial', 'error'];

export const WORKSPACE_ROUTE_GROUPS = /** @type {const} */ ([
  ['INTELLIGENCE', ['dashboard', 'ask']],
  ['IP ANALYSIS', ['patentability', 'prior-art', 'tk-risk']],
  ['REGULATION', ['regulation-compare', 'document-checker', 'regulation-changes', 'compliance-journey', 'regulatory-alerts']],
  ['WORKSPACE', ['knowledge-library', 'reports', 'settings']],
]);

export const WORKSPACE_ROUTE_ORDER = WORKSPACE_ROUTE_GROUPS.flatMap(([, routes]) => routes);

const WORKSPACE_ROUTE_SET = new Set(WORKSPACE_ROUTE_ORDER);

export function normalizeSceneRoute(value) {
  if (typeof value !== 'string') return '';
  const route = value.split('?')[0].split('#')[0].split('/').filter(Boolean)[0] || '';
  return WORKSPACE_ROUTE_SET.has(route) ? route : '';
}

export function sceneTransitionDirection(fromRoute, toRoute) {
  const from = WORKSPACE_ROUTE_ORDER.indexOf(normalizeSceneRoute(fromRoute));
  const to = WORKSPACE_ROUTE_ORDER.indexOf(normalizeSceneRoute(toRoute));
  if (from < 0 || to < 0 || from === to) return 0;
  return to > from ? 1 : -1;
}

export function createSceneTransitionState(route = '') {
  const normalized = normalizeSceneRoute(route);
  return {
    route: normalized,
    fromRoute: normalized,
    toRoute: normalized,
    transitionStartedAt: 0,
    direction: 0,
    transitionRevision: 0,
  };
}

export function reduceSceneTransition(state, toRoute, at, confirmation = false) {
  const target = normalizeSceneRoute(toRoute);
  if (!target) return state;

  if (!state.route) {
    return { ...state, route: target, fromRoute: target, toRoute: target, transitionStartedAt: 0, direction: 0 };
  }

  if (confirmation && state.toRoute === target) {
    return state.route === target ? state : { ...state, route: target };
  }

  // A superseded Next navigation can confirm after a newer click. Keep the
  // latest target authoritative instead of briefly queueing the stale route.
  if (confirmation && state.toRoute && state.toRoute !== state.route && state.toRoute !== target) return state;

  if (!confirmation && (state.toRoute || state.route) === target) return state;
  if (confirmation && state.route === target) return state;

  const fromRoute = state.route;
  return {
    ...state,
    route: confirmation ? target : state.route,
    fromRoute,
    toRoute: target,
    transitionStartedAt: at,
    direction: sceneTransitionDirection(fromRoute, target),
    transitionRevision: state.transitionRevision + 1,
  };
}

export function normalizeSceneCount(value, cap = 15) {
  if (value === null || value === undefined || value === '') return undefined;
  const numeric = typeof value === 'number' ? value : Number(value);
  if (!Number.isFinite(numeric) || numeric < 0) return undefined;
  return Math.min(Math.floor(numeric), Math.max(0, Math.floor(cap)));
}

export function normalizeSceneScore(value) {
  if (value === null || value === undefined || value === '') return undefined;
  const numeric = typeof value === 'number' ? value : Number(value);
  if (!Number.isFinite(numeric) || numeric < 0) return undefined;
  const ratio = numeric > 1 ? numeric / 100 : numeric;
  return Math.min(1, ratio);
}

export function normalizeJurisdictions(value) {
  if (!Array.isArray(value)) return [];
  return [...new Set(value.filter((item) => typeof item === 'string').map((item) => item.trim().toUpperCase()).filter(Boolean))].slice(0, 4);
}

export function normalizeProviderTone(value) {
  return ['ready', 'partial', 'unavailable', 'neutral'].includes(value) ? value : 'neutral';
}

export function normalizeRiskTone(value) {
  return ['low', 'medium', 'high'].includes(value) ? value : undefined;
}

const signal = {
  ...createSceneTransitionState(),
  phase: 'idle',
  phaseStartedAt: 0,
  pulseAt: 0,
  pulseKind: 'none',
  nodeCount: undefined,
  density: undefined,
  score: undefined,
  jurisdictions: [],
  hover: '',
  providerTone: 'neutral',
  riskTone: undefined,
  documentSelected: false,
};

function now() {
  return typeof performance !== 'undefined' ? performance.now() : Date.now();
}

export function getSceneSignal() {
  return signal;
}

export function setSceneRoute(route) {
  const transition = reduceSceneTransition(signal, route, now(), true);
  if (transition === signal) return;
  const routeChanged = signal.route !== transition.route;
  Object.assign(signal, transition);
  if (!routeChanged) return;
  signal.phase = 'idle';
  signal.phaseStartedAt = now();
  signal.nodeCount = undefined;
  signal.density = undefined;
  signal.score = undefined;
  signal.jurisdictions = [];
  signal.hover = '';
  signal.providerTone = 'neutral';
  signal.riskTone = undefined;
  signal.documentSelected = false;
}

export function beginSceneTransition(toRoute) {
  const transition = reduceSceneTransition(signal, toRoute, now(), false);
  if (transition === signal) return false;
  Object.assign(signal, transition);
  return true;
}

export function setScenePhase(phase, pulseKind = phase) {
  if (!SCENE_PHASES.includes(phase)) return;
  const timestamp = now();
  signal.phase = phase;
  signal.phaseStartedAt = timestamp;
  if (phase === 'submitting' || phase === 'success' || phase === 'partial' || phase === 'error') {
    signal.pulseAt = timestamp;
    signal.pulseKind = pulseKind;
  }
}

export function pulseScene(kind = 'activity') {
  signal.pulseAt = now();
  signal.pulseKind = kind;
}

export function setSceneMetrics(patch = {}) {
  if ('nodeCount' in patch) signal.nodeCount = normalizeSceneCount(patch.nodeCount, 15);
  if ('density' in patch) signal.density = normalizeSceneCount(patch.density, 88);
  if ('score' in patch) signal.score = normalizeSceneScore(patch.score);
  if ('jurisdictions' in patch) signal.jurisdictions = normalizeJurisdictions(patch.jurisdictions);
  if ('providerTone' in patch) signal.providerTone = normalizeProviderTone(patch.providerTone);
  if ('riskTone' in patch) signal.riskTone = normalizeRiskTone(patch.riskTone);
  if ('documentSelected' in patch) signal.documentSelected = patch.documentSelected === true;
}

export function setSceneHover(value = '') {
  signal.hover = typeof value === 'string' ? value.slice(0, 48) : '';
}
