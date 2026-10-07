const SECRET_KEY_PATTERN = /(?:api[_-]?key|secret|token|password|passwd|authorization|cookie|credential|session)/i;

const ACRONYMS = new Map([
  ['ayush', 'AYUSH'],
  ['tk', 'TK'],
  ['tkdl', 'TKDL'],
]);

function present(value) {
  return value !== null && value !== undefined && value !== '';
}

function scalar(value) {
  if (typeof value === 'boolean') return value ? 'Yes' : 'No';
  if (typeof value === 'number' && Number.isFinite(value)) return String(value);
  if (typeof value === 'string') return value;
  return null;
}

export function humanizeResultLabel(value) {
  const words = String(value ?? '').trim().replaceAll('_', ' ').replaceAll('-', ' ').split(/\s+/).filter(Boolean);
  return words.map((word, index) => ACRONYMS.get(word.toLowerCase()) || (index === 0 ? `${word.charAt(0).toUpperCase()}${word.slice(1).toLowerCase()}` : word.toLowerCase())).join(' ');
}

export function statusTone(value) {
  const status = String(value ?? '').trim().toLowerCase().replaceAll('_', ' ').replaceAll('-', ' ');
  if (/failed|failure|error|rejected|invalid/.test(status)) return 'failed';
  if (/unavailable|unconfigured|missing|not available|not performed|not assessed|not configured|not verified|unknown/.test(status)) return 'unavailable';
  if (/partial|insufficient|pending|warning|conflict|review|required|incomplete/.test(status)) return 'partial';
  if (/completed|complete|success|succeeded|grounded|screened|passed|available|ready|original/.test(status)) return 'completed';
  return 'neutral';
}

export function buildTechnicalRows(result) {
  if (!Array.isArray(result?.trace)) return [];
  return result.trace.flatMap((item, index) => {
    if (!item || typeof item !== 'object' || !present(item.agent) || !present(item.status)) return [];
    return [{
      key: `${String(item.agent)}-${String(item.status)}-${index}`,
      label: humanizeResultLabel(item.agent),
      value: humanizeResultLabel(item.status),
      tone: statusTone(item.status),
    }];
  });
}

export function citationDisplayEntries(citations) {
  if (!Array.isArray(citations)) return [];
  return citations.map((citation, index) => {
    const backendId = present(citation?.citation_id) ? citation.citation_id : index + 1;
    const source = citation?.title || citation?.source || 'Retrieved source';
    return {
      citation,
      backendId,
      marker: `[${String(backendId)}]`,
      source,
      key: `${String(backendId)}:${String(citation?.source_url || source)}:${index}`,
    };
  });
}

function addRow(rows, label, value) {
  const normalized = scalar(value);
  if (normalized !== null && normalized !== '') rows.push({label, value: normalized});
}

export function buildStructuredInspection(result, data = result) {
  const root = result && typeof result === 'object' ? result : {};
  const primary = data && typeof data === 'object' ? data : root;
  const sections = [];

  const overview = [];
  const status = root.status ?? primary.status;
  const mode = root.mode ?? primary.mode ?? primary.search_summary?.provider_mode;
  addRow(overview, 'Status', present(status) ? humanizeResultLabel(status) : null);
  addRow(overview, 'Mode', present(mode) ? humanizeResultLabel(mode) : null);
  addRow(overview, 'Question', root.question ?? primary.question);
  addRow(overview, 'Answer', root.answer ?? primary.answer);
  const outputLanguage = root.output_language ?? primary.output_language;
  addRow(overview, 'Output language', present(outputLanguage) ? String(outputLanguage).toUpperCase() : null);
  if (overview.length) sections.push({id: 'overview', title: 'Result overview', rows: overview, items: []});

  const citations = Array.isArray(root.citations) && root.citations.length ? root.citations : (Array.isArray(primary.citations) ? primary.citations : []);
  if (citations.length) {
    const citationItems = citationDisplayEntries(citations).map(({marker, source, citation}) => {
      const page = present(citation.page) ? ` · Page ${String(citation.page)}` : '';
      return `${marker} ${source}${page}`;
    });
    sections.push({id: 'citations', title: `Citation map (${citations.length})`, rows: [], items: citationItems});
  }

  const trust = root.trust && typeof root.trust === 'object' ? root.trust : (primary.trust && typeof primary.trust === 'object' ? primary.trust : null);
  if (trust) {
    const evidence = [];
    addRow(evidence, 'Trust score', present(trust.trust_score) ? `${String(trust.trust_score)}/100` : null);
    addRow(evidence, 'Evidence score', present(trust.evidence_score) ? `${String(trust.evidence_score)}/100` : null);
    addRow(evidence, 'Trust level', present(trust.level) ? humanizeResultLabel(trust.level) : null);
    addRow(evidence, 'Hallucination risk', present(trust.hallucination_risk) ? humanizeResultLabel(trust.hallucination_risk) : null);
    addRow(evidence, 'Contradictions detected', trust.contradictions_detected);
    addRow(evidence, 'Unsupported claims', trust.unsupported_claims);
    addRow(evidence, 'Trust note', trust.disclaimer);
    if (evidence.length) sections.push({id: 'evidence', title: 'Evidence summary', rows: evidence, items: []});
  }

  const seenLimitations = new Set();
  const limitations = [...(Array.isArray(root.limitations) ? root.limitations : []), ...(primary !== root && Array.isArray(primary.limitations) ? primary.limitations : [])]
    .filter((value) => {
      if (typeof value !== 'string' || !value.trim()) return false;
      const key = value.trim().toLocaleLowerCase();
      if (seenLimitations.has(key)) return false;
      seenLimitations.add(key);
      return true;
    });
  if (limitations.length) sections.push({id: 'limitations', title: `Limitations (${limitations.length})`, rows: [], items: limitations});

  const technicalRows = buildTechnicalRows(root);
  if (technicalRows.length) sections.push({id: 'pipeline', title: 'Pipeline checks', rows: technicalRows.map(({label, value}) => ({label, value})), items: []});

  return sections;
}

export function shouldShowDeveloperJson(value) {
  return value === 'true';
}

export function sanitizeDeveloperPayload(value, seen = new WeakSet()) {
  if (Array.isArray(value)) return value.map((item) => sanitizeDeveloperPayload(item, seen));
  if (!value || typeof value !== 'object') return value;
  if (seen.has(value)) return '[Circular]';
  seen.add(value);
  const sanitized = {};
  for (const [key, item] of Object.entries(value)) {
    sanitized[key] = SECRET_KEY_PATTERN.test(key) ? '[REDACTED]' : sanitizeDeveloperPayload(item, seen);
  }
  seen.delete(value);
  return sanitized;
}
