export const SCENE_PHASES = ['idle', 'input', 'submitting', 'processing', 'success', 'partial', 'error'];

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
  route: 'dashboard',
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
  if (!route || signal.route === route) return;
  signal.route = route;
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
