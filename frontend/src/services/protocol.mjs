export function safeSourceUrl(value) {
  if (typeof value !== 'string') return null;
  try { const url = new URL(value); return ['https:', 'http:'].includes(url.protocol) && !url.username && !url.password ? url.href : null; } catch { return null; }
}
export function describeMode(mode) {
  return ({mock:'Synthetic test data',live:'Live provider mode',local:'Local source material',unconfigured:'No provider configured'})[mode] || 'Source mode unavailable';
}
export function clampScore(score) {
  return typeof score === 'number' && Number.isFinite(score) ? Math.max(0,Math.min(100,score)) : null;
}
export async function decodeResponse(response) {
  let data;
  try { data = await response.json(); } catch { throw new Error(`The API returned unreadable data (HTTP ${response.status}).`); }
  if (!response.ok) {
    const detail = typeof data.detail === 'string' ? data.detail : Array.isArray(data.detail) ? data.detail.map(x => `${(x.loc || []).slice(1).join('.')}: ${x.msg}`).join('; ') : `Request failed (HTTP ${response.status}).`;
    throw new Error(detail);
  }
  return data;
}
