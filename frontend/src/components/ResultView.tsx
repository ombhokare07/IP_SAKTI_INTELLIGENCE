'use client';

import {useState} from 'react';
import CitationCard from './CitationCard';
import ConfidenceScore from './ConfidenceScore';
import RiskMeter from './RiskMeter';
import ComparisonTable from './ComparisonTable';
import {describeMode, safeSourceUrl} from '@/services/protocol.mjs';

const text = (value: unknown): string => typeof value === 'string' ? value : JSON.stringify(value);
const human = (value: unknown): string => String(value ?? '').replaceAll('_', ' ');
const present = (value: unknown) => value !== null && value !== undefined && value !== '';

function uniqueText(values: unknown[]): string[] {
  const seen = new Set<string>();
  return values.flatMap((value) => Array.isArray(value) ? value : [value]).map(text).filter((value) => {
    const key = value.trim().toLocaleLowerCase();
    if (!key || seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

export function Notice({children, type = 'notice'}: {children: React.ReactNode; type?: string}) {
  return <div className={`notice ${type}`} role={type === 'error' ? 'alert' : 'status'}>{children}</div>;
}

type EmptyAction = {label: string; href?: string; onClick?: () => void};
export function Empty({title = 'No assessment yet', children, action}: {title?: string; children?: React.ReactNode; action?: EmptyAction}) {
  const defaults: Record<string, EmptyAction> = {
    'No assessment yet': {label: 'Complete screening form', href: '#screening-form'},
    'No saved reports yet': {label: 'Start a screening', href: '/ask'},
    'No stored changes to compare': {label: 'Open source library', href: '/knowledge-library'},
    'No records returned': {label: 'Refine screening', href: '#screening-form'},
    'No requirements to screen': {label: 'Compare regulations', href: '/regulation-compare'},
  };
  const resolvedAction = action || defaults[title];
  return <div className="empty-state">
    <span className="empty-icon" aria-hidden="true">◇</span>
    <strong>{title}</strong>
    <p>{children || 'Enter your information and run a screen. Evidence and limitations will appear here.'}</p>
    {resolvedAction && (resolvedAction.onClick
      ? <button className="button primary small empty-cta" onClick={resolvedAction.onClick}>{resolvedAction.label}</button>
      : <a className="button primary small empty-cta" href={resolvedAction.href}>{resolvedAction.label}</a>)}
  </div>;
}

function CollapsibleList({items, label, limit = 4}: {items: unknown[]; label: string; limit?: number}) {
  const [expanded, setExpanded] = useState(false);
  const normalized = uniqueText(items);
  const visible = expanded ? normalized : normalized.slice(0, limit);
  return <div className="collapsible-list">
    <ul className="checklist">{visible.map((item) => <li key={item}>{item}</li>)}</ul>
    {normalized.length > limit && <button className="text-button" type="button" onClick={() => setExpanded((current) => !current)} aria-expanded={expanded}>
      {expanded ? `Show fewer ${label.toLowerCase()}` : `View all ${label.toLowerCase()} (${normalized.length})`}
    </button>}
  </div>;
}

type ResultKind = 'patentability' | 'prior-art' | 'tk-risk' | 'regulation' | 'document' | 'journey' | 'general';

function resultKind(data: any): ResultKind {
  if (data?.steps) return 'journey';
  if (data?.checks) return 'document';
  if (data?.rows) return 'regulation';
  if (Object.hasOwn(data || {}, 'search_performed') || Object.hasOwn(data || {}, 'authorized_search_performed') || Object.hasOwn(data || {}, 'tkdl_access')) return 'tk-risk';
  if (Array.isArray(data?.results) && data?.search_summary) return 'prior-art';
  if (data?.assessment?.novelty || data?.assessment?.inventive_step) return 'patentability';
  return 'general';
}

function summaryTitle(kind: ResultKind): string {
  return ({
    patentability: 'Patentability screening',
    'prior-art': 'Prior-art search',
    'tk-risk': 'Traditional knowledge review',
    regulation: 'Regulation comparison',
    document: 'Document compliance screen',
    journey: 'Compliance journey',
    general: 'Evidence-grounded response',
  } as Record<ResultKind, string>)[kind];
}

function Summary({result, data, trust, patent, kind}: {result: any; data: any; trust: any; patent: any; kind: ResultKind}) {
  const tkAuthorized = data.authorized_search_performed === true || data.risk?.authorized_search_performed === true;
  const tkSearched = data.search_performed === true;
  const rows = Array.isArray(data.rows) ? data.rows : [];
  const checks = Array.isArray(data.checks) ? data.checks : [];
  const steps = Array.isArray(data.steps) ? data.steps : [];
  const coverage = Object.values(data.coverage || {});
  const findings: [string, string][] = [];

  if (kind === 'patentability') {
    if (data.assessment?.novelty) findings.push(['Novelty', human(data.assessment.novelty.status || data.assessment.novelty.summary)]);
    if (data.assessment?.inventive_step) findings.push(['Inventive step', human(data.assessment.inventive_step.status || data.assessment.inventive_step.summary)]);
    findings.push(['Prior-art evidence', data.prior_art?.search_summary ? 'Search results attached' : 'Separate search required']);
  } else if (kind === 'prior-art') {
    findings.push(['Provider', describeMode(data.search_summary?.provider_mode || data.mode)]);
    findings.push(['Records returned', String(data.results?.length || 0)]);
    findings.push(['Search status', data.search_summary ? 'Completed against configured provider' : 'Not performed']);
  } else if (kind === 'tk-risk') {
    findings.push(['Provider search', tkSearched ? 'Performed' : 'Not performed']);
    findings.push(['Authorized search', tkAuthorized ? 'Performed' : 'Not performed']);
    findings.push(['Overlap status', tkSearched ? human(data.overlap_status || 'not evaluated') : 'Not evaluated']);
    findings.push(['TK clearance', tkAuthorized ? human(data.clearance_status || 'cannot be issued') : 'Not assessed']);
  } else if (kind === 'regulation') {
    findings.push(['Jurisdictions', String(data.jurisdictions?.length || Object.keys(data.coverage || {}).length)]);
    findings.push(['Evidence coverage', coverage.length ? `${coverage.filter(Boolean).length} of ${coverage.length} jurisdictions` : 'Not assessed']);
    findings.push(['Comparable requirements', String(rows.length)]);
  } else if (kind === 'document') {
    const missing = checks.filter((check: any) => ['missing', 'rule_mismatch'].includes(check.status)).length;
    findings.push(['Fields assessed', String(checks.length)]);
    findings.push(['Observed or satisfied', String(Math.max(0, checks.length - missing))]);
    findings.push(['Needs review', String(missing)]);
  } else if (kind === 'journey') {
    findings.push(['Journey steps', String(steps.length)]);
    findings.push(['Pending steps', String(steps.filter((step: any) => !['complete', 'completed', 'satisfied'].includes(step.status)).length)]);
    findings.push(['Dependencies', String(steps.reduce((count: number, step: any) => count + (step.depends_on?.length || 0), 0))]);
  }

  let answer = result.answer || data.risk?.conclusion || 'Review the available evidence, important gaps and recommended next action below.';
  if (kind === 'tk-risk' && !tkAuthorized) answer = 'Cannot be determined — authorized TK search not performed. TK clearance is not assessed.';
  if (kind === 'regulation' && !rows.length && coverage.every((value) => !value)) answer = 'No configured regulatory evidence was available for this comparison. This does not mean no requirement applies.';

  const status = human(result.status || data.status || 'screening');
  const caution = /insufficient|unconfigured|not configured|failed|unavailable|not assessed/.test(status.toLowerCase());

  return <section className={`result-summary result-summary--${kind}`} aria-labelledby="result-summary-title">
    <div className="section-title">
      <div><span className="eyebrow">RESULT SUMMARY</span><h2 id="result-summary-title">{summaryTitle(kind)}</h2></div>
      <span className={`badge${caution ? ' warning' : ''}`}>{status}</span>
    </div>
    <p className="answer-text">{answer}</p>
    {(trust || patent || data.risk || data.score) && <div className="score-grid">
      {trust && <ConfidenceScore label="Trust" score={trust.trust_score} description="Grounding quality, not legal correctness."/>}
      {trust && <ConfidenceScore label="Evidence" score={trust.evidence_score} description="Coverage and quality of available evidence."/>}
      {patent && <ConfidenceScore label="Readiness" score={patent.score} description="Screening completeness, not probability of grant."/>}
      {data.score && <ConfidenceScore score={data.score.score} label={data.score.name} description={data.score.meaning}/>}
      {data.risk && <RiskMeter score={data.risk.score} level={data.risk.level} label={data.risk.name || 'Detected overlap'}/>}
    </div>}
    {findings.length > 0 && <div className="finding-grid"><h3>Key findings</h3>{findings.slice(0, 5).map(([label, value]) => <div className="finding-item" key={label}><strong>{label}</strong><span>{value || 'Needs review'}</span></div>)}</div>}
  </section>;
}

function importantGaps(data: any, kind: ResultKind): string[] {
  const gaps: unknown[] = [...(data.evidence_gaps || [])];
  if (kind === 'tk-risk' && data.authorized_search_performed !== true && data.risk?.authorized_search_performed !== true) {
    gaps.push('Authorized traditional-knowledge search was not performed; final TK clearance cannot be issued.');
  }
  if (kind === 'regulation') {
    Object.entries(data.coverage || {}).forEach(([jurisdiction, covered]) => {
      if (!covered) gaps.push(`No configured regulatory evidence was available for ${jurisdiction}.`);
    });
  }
  if (kind === 'document') {
    (data.checks || []).filter((check: any) => ['missing', 'rule_mismatch'].includes(check.status)).forEach((check: any) => gaps.push(`${check.label}: ${human(check.status)}.`));
  }
  return uniqueText(gaps);
}

function recommendedSteps(data: any, kind: ResultKind): string[] {
  const supplied = uniqueText(data.recommended_next_steps || []);
  if (supplied.length) return supplied;
  if (kind === 'tk-risk' && data.authorized_search_performed !== true && data.risk?.authorized_search_performed !== true) {
    return ['Arrange a search of an operator-authorized traditional-knowledge corpus and retain its source record.'];
  }
  if (kind === 'regulation' && (!data.rows || data.rows.length === 0)) {
    return ['Configure and verify a dated regulatory evidence source before drawing a jurisdictional conclusion.'];
  }
  return [];
}

export default function ResultView({result}: {result: any}) {
  if (!result) return <Empty/>;
  const nested = result.routing ? result.results?.[result.routing.primary] : null;
  const data = nested || result;
  const kind = resultKind(data);
  const mode = data.mode || data.search_summary?.provider_mode || result.mode || 'local';
  const citations = result.citations?.length ? result.citations : data.citations || [];
  const trust = result.trust || data.trust;
  const patent = data.assessment?.readiness;
  const prior = Array.isArray(data.results) && data.search_summary ? data.results : null;
  const limitations = uniqueText([result.limitations || [], data.limitations || []]);
  const gaps = importantGaps(data, kind);
  const nextSteps = recommendedSteps(data, kind);
  const hasTechnicalDetails = result && typeof result === 'object' && Object.keys(result).length > 0;

  return <div className={`result-view result-view--${kind}`}>
    <div className="result-top"><h2>Screening result</h2><span className={`badge${mode === 'mock' ? ' warning' : ''}`}>{describeMode(mode)}</span></div>
    {mode === 'mock' && <Notice type="warning"><strong>Test data only.</strong> These records demonstrate the workflow and are not real patents, regulations or TKDL evidence.</Notice>}
    <Summary result={result} data={data} trust={trust} patent={patent} kind={kind}/>

    {data.extracted && <details className="panel inset result-section"><summary>Extracted from your description</summary><div className="extraction-grid">{Object.entries(data.extracted).map(([key, items]) => <div key={key}><span className="field-label">{human(key)}</span><div className="chips">{Array.isArray(items) && items.length ? items.map((item: any, index: number) => <span className="chip" key={`${key}-${index}`}>{item.canonical || text(item)}{item.negated ? ' · negated mention' : ''}{item.original && item.original !== item.canonical ? <small>{item.original}</small> : null}</span>) : <span className="muted">No recognized mention</span>}</div></div>)}</div></details>}
    {data.invention && <details className="panel inset result-section"><summary>Invention profile</summary><dl className="details-grid compact-details">{Object.entries(data.invention).filter(([, value]) => value && (!Array.isArray(value) || value.length)).map(([key, value]) => <div key={key}><dt>{human(key)}</dt><dd>{Array.isArray(value) ? value.join(' · ') : text(value)}</dd></div>)}</dl></details>}

    {data.assessment?.novelty && <section className="result-section evidence-findings"><div className="section-title"><div><span className="eyebrow">ASSESSMENT</span><h3>Key findings</h3></div></div><div className="two-columns">{['novelty', 'inventive_step'].map((key) => data.assessment[key] && <article className="finding-detail" key={key}><span className="field-label">{human(key)}</span><strong>{human(data.assessment[key].status || 'Needs review')}</strong><p>{data.assessment[key].summary || data.assessment[key].explanation || 'No narrative assessment was supplied.'}</p></article>)}</div></section>}

    {gaps.length > 0 && <section className="result-section action-section gap-section"><div className="section-title"><div><span className="eyebrow">REVIEW BEFORE RELYING</span><h3>Important gaps</h3></div><span className="count">{gaps.length}</span></div><CollapsibleList items={gaps} label="important gaps"/></section>}
    {nextSteps.length > 0 && <section className="result-section action-section next-step-section"><div className="section-title"><div><span className="eyebrow">WHAT TO DO NEXT</span><h3>Recommended next steps</h3></div></div><CollapsibleList items={nextSteps} label="next steps" limit={5}/></section>}

    {prior && <section className="result-section grouped-result result-records"><div className="section-title"><div><span className="eyebrow">SEARCH OUTPUT</span><h3>Patent and source matches</h3></div><span className="count">{prior.length}</span></div>{!prior.length && <Empty title="No records returned">A search with no results does not establish novelty.</Empty>}{prior.map((item: any, index: number) => <article className="patent-record" key={item.publication_number || index}><div className="row-between"><span className="eyebrow">RANK {item.rank || index + 1} · {item.publication_number || 'Identifier unavailable'}</span><span className="badge">Similarity {item.similarity?.overall_similarity ?? '—'}/100</span></div><h3>{item.title || 'Title unavailable'}</h3><p>{item.abstract || item.relevance_summary || 'Abstract unavailable from this provider.'}</p><div className="meta-row"><span>{item.jurisdiction || 'Jurisdiction unavailable'}</span><span>Published: {item.publication_date || 'Unavailable'}</span>{item.provider && <span>{item.provider}</span>}</div>{item.feature_overlap?.matching_features?.length > 0 && <div className="chips">{item.feature_overlap.matching_features.map((feature: string) => <span className="chip" key={feature}>{feature}</span>)}</div>}{safeSourceUrl(item.source_url) ? <a href={safeSourceUrl(item.source_url)!} target="_blank" rel="noreferrer">Open supplied source <span aria-hidden="true">↗</span></a> : <small>No source URL was supplied. Use the publication identifier to inspect the record.</small>}</article>)}</section>}

    {kind === 'tk-risk' && data.search_performed === true && data.matches?.length === 0 && <section className="result-section action-section"><Empty title="No review leads in the configured source">This does not establish absence of traditional knowledge and does not provide TK clearance.</Empty></section>}
    {data.matches?.length > 0 && <section className="result-section grouped-result"><div className="section-title"><div><span className="eyebrow">OVERLAP REVIEW</span><h3>Traditional knowledge review leads</h3></div><span className="count">{data.matches.length}</span></div>{data.matches.map((match: any, index: number) => <article className="panel inset" key={match.record_id || index}><div className="row-between"><strong>{match.record_id || 'Record identifier unavailable'}</strong><span className="badge">Feature overlap {match.similarity?.score ?? '—'}/100</span></div>{match.similarity?.features && <div className="chips">{Object.values(match.similarity.features).flatMap((feature: any) => feature.matched || []).map((value: any, itemIndex: number) => <span className="chip" key={`${value}-${itemIndex}`}>{value}</span>)}</div>}<CitationCard citation={match.evidence || {}} index={index}/></article>)}</section>}
    {data.rows && <section className="result-section grouped-result"><div className="section-title"><div><span className="eyebrow">JURISDICTION REVIEW</span><h3>Requirement and evidence status</h3></div></div>{data.coverage && <div className="chips">{Object.entries(data.coverage).map(([jurisdiction, covered]) => <span className={`chip${!covered ? ' warning' : ''}`} key={jurisdiction}>{jurisdiction}: {covered ? 'Stored evidence available' : 'Evidence missing'}</span>)}</div>}<ComparisonTable rows={data.rows} jurisdictions={data.jurisdictions || Object.keys(data.coverage || {})}/></section>}
    {data.checks && <section className="result-section grouped-result"><div className="section-title"><div><span className="eyebrow">FIELD REVIEW</span><h3>Assessed document fields</h3></div></div>{data.checks.length ? <div className="table-scroll"><table><thead><tr><th>Requirement</th><th>Supplied information</th><th>Screening status</th><th>Evidence</th></tr></thead><tbody>{data.checks.map((check: any, index: number) => <tr key={check.field || check.label || index}><th>{check.label}</th><td>{present(check.supplied_value) ? text(check.supplied_value) : '—'}</td><td><span className={`badge${check.status === 'missing' || check.status === 'rule_mismatch' ? ' warning' : ''}`}>{human(check.status)}</span></td><td>{check.evidence_id || 'Not supplied'}{check.version && <small>{check.version}</small>}</td></tr>)}</tbody></table></div> : <Empty title="No requirements to screen">Supply a current, applicable regulatory corpus. This is not a compliance clearance.</Empty>}</section>}
    {data.steps && <section className="result-section grouped-result journey-section"><div className="section-title"><div><span className="eyebrow">REVIEW SEQUENCE</span><h3>Your compliance journey</h3></div></div><ol className="journey">{data.steps.map((step: any, index: number) => <li key={step.id || index}><span>{String(index + 1).padStart(2, '0')}</span><div><strong>{step.title}</strong><small>{human(step.status)}{step.depends_on?.length ? ` · After: ${step.depends_on.join(', ')}` : ''}</small>{step.evidence_ids?.length > 0 && <p className="muted">Evidence: {step.evidence_ids.join(', ')}</p>}</div></li>)}</ol></section>}

    {result.routing && Object.keys(result.results || {}).length > 1 && <details className="result-section grouped-result"><summary>Additional screening results</summary>{Object.entries(result.results).filter(([name]) => name !== result.routing.primary).map(([name, value]) => <details className="panel inset" key={name}><summary>{human(name)}</summary><ResultView result={value}/></details>)}</details>}

    <section className="result-section sources-section"><div className="section-title"><div><span className="eyebrow">SUPPORTING MATERIAL</span><h3>Evidence &amp; sources</h3></div><span className="count">{citations.length} source{citations.length === 1 ? '' : 's'}</span></div>{citations.length > 0 ? <div className="source-grid"><CitationCollection citations={citations}/></div> : <Notice>No source excerpts are available for this result. No definitive conclusion should be drawn.</Notice>}</section>
    {limitations.length > 0 && <details className="limitations result-section"><summary>Limitations <span className="count">{limitations.length}</span></summary><ul>{limitations.map((value) => <li key={value}>{value}</li>)}</ul></details>}
    {hasTechnicalDetails && <details className="raw-detail"><summary>Technical details</summary>{result.trace?.length > 0 && <div className="trace">{result.trace.map((trace: any, index: number) => <span key={index}>{human(trace.agent)}<small>{human(trace.status)}</small></span>)}</div>}<details className="structured-response"><summary>View structured response</summary><pre>{JSON.stringify(result, null, 2)}</pre></details></details>}
    <p className="screening-disclaimer">This workspace supports evidence screening. It does not provide legal advice, regulatory clearance or a probability of patent grant.</p>
  </div>;
}

function CitationCollection({citations}: {citations: any[]}) {
  const [expanded, setExpanded] = useState(false);
  const visible = expanded ? citations : citations.slice(0, 5);
  return <>{visible.map((citation, index) => <CitationCard key={citation.citation_id || citation.source_url || `${citation.title || 'source'}-${index}`} citation={citation} index={index}/>)}{citations.length > 5 && <button className="text-button" type="button" onClick={() => setExpanded((current) => !current)} aria-expanded={expanded}>{expanded ? 'Show top five' : `View all ${citations.length} sources`}</button>}</>;
}
