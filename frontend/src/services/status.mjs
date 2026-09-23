const POSITIVE_STATES = new Set(['ready', 'live', 'local', 'connected', 'available', 'initialized', 'indexed', 'enabled']);

export function statusCode(value) {
  const raw = value && typeof value === 'object' ? value.status : value;
  return String(raw ?? 'unavailable').trim().toLowerCase().replace(/\s+/g, '_');
}

export function describeStatus(value) {
  if (
    value &&
    typeof value === 'object' &&
    typeof value.code === 'string' &&
    typeof value.label === 'string' &&
    ['positive', 'attention', 'negative'].includes(value.tone)
  ) {
    return value;
  }
  const code = statusCode(value);
  const labels = {
    ready: 'Ready',
    live: 'Live',
    local: 'Local',
    connected: 'Connected',
    available: 'Available',
    initialized: 'Initialized',
    indexed: 'Indexed',
    enabled: 'Enabled',
    configured: 'Configured',
    configured_not_verified: 'Configured · not verified',
    partial: 'Partial',
    degraded: 'Partial',
    authorization_required: 'Authorization required',
    mock: 'Synthetic test data',
    synthetic: 'Synthetic test data',
    unavailable: 'Unavailable',
    unconfigured: 'Needs configuration',
    not_configured: 'Needs configuration',
    not_connected: 'Not connected',
    empty: 'Empty',
    not_indexed: 'Not indexed',
    disabled: 'Disabled',
    running: 'Running',
  };
  const label = labels[code] || code.replaceAll('_', ' ').replace(/^./, (letter) => letter.toUpperCase());
  const connected = POSITIVE_STATES.has(code);
  const tone = connected
    ? 'positive'
    : ['configured', 'configured_not_verified', 'partial', 'degraded', 'authorization_required', 'mock', 'synthetic', 'empty', 'not_indexed'].includes(code)
      ? 'attention'
      : 'negative';
  return { code, label, tone, connected };
}

export function isVerifiedConnection(value) {
  return describeStatus(value).connected;
}

export function authSessionStatus(status) {
  const auth = status?.authentication || status?.provider_status?.authentication;
  if (!auth) return describeStatus('unavailable');
  const google = statusCode(auth.google_sign_in);
  const cookie = statusCode(auth.session_cookie);
  if (['configured', 'ready'].includes(google) && ['configured', 'ready'].includes(cookie)) {
    return { code: 'configured', label: 'Google session configured', tone: 'positive', connected: true };
  }
  return { code: 'not_configured', label: 'Google session not configured', tone: 'negative', connected: false };
}

export function countConnectedProviders(providers) {
  return Object.values(providers || {}).filter((value) => describeStatus(value).connected).length;
}

export function summarizeProviders(providers) {
  const values = Object.values(providers || {});
  const connected = countConnectedProviders(providers);
  if (!values.length) return { connected: 0, total: 0, label: 'Status unavailable', tone: 'negative' };
  if (!connected) return { connected, total: values.length, label: 'No verified providers', tone: 'attention' };
  return { connected, total: values.length, label: `${connected} verified / connected`, tone: 'positive' };
}
