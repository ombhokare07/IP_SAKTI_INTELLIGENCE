'use client';

import { type FormEvent, useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { AlertTriangle, ArrowUpRight, BookOpenCheck, Check, FileText, Headphones, LoaderCircle, Mic, Save, Search, ShieldAlert, Sparkles } from 'lucide-react';
import { motion, useReducedMotion } from 'framer-motion';
import ChatBox from '@/components/ChatBox';
import ResultView, { Notice } from '@/components/ResultView';
import { ErrorState, PageHeader } from '@/components/ui/WorkspaceUI';
import { api } from '@/services/api';
import { useResource } from '@/hooks/useResource';
import { invalidateResource } from '@/services/resource-cache';
import { pulseScene, setSceneMetrics, setScenePhase } from '@/services/scene-signals.mjs';
import type { DocumentsResponse, PriorArtSearchResult } from '@/types/api';

export type ScreeningPageName = 'ask' | 'patentability' | 'prior-art' | 'tk-risk' | 'regulation-compare' | 'document-checker' | 'compliance-journey';

const CONFIG: Record<ScreeningPageName, { description: string; endpoint: string; kind: 'ask' | 'patent' | 'prior_art' | 'traditional_knowledge' | 'comparison' | 'compliance' | 'journey'; button: string }> = {
  ask: { description: 'Ask a precise question, choose the intended research route, and inspect every supporting source and limitation.', endpoint: '/agents/run', kind: 'ask', button: 'Ask IP-SAKTI' },
  patentability: { description: 'Screen an invention for novelty, inventive-step questions and evidence gaps — never a probability of grant.', endpoint: '/patentability/screen', kind: 'patent', button: 'Run patentability screen' },
  'prior-art': { description: 'Search the configured patent provider and review completeness, overlap and partial-search limitations.', endpoint: '/prior-art/search', kind: 'prior_art', button: 'Search prior art' },
  'tk-risk': { description: 'Review traditional-knowledge overlap with authorization, corpus scope and TKDL connectivity kept explicit.', endpoint: '/traditional-knowledge/assess', kind: 'traditional_knowledge', button: 'Assess TK risk' },
  'regulation-compare': { description: 'Compare dated requirements across India, the USA, the EU and the UK using backend evidence only.', endpoint: '/regulations/compare', kind: 'comparison', button: 'Compare regulations' },
  'document-checker': { description: 'Check pasted text or a stored document against the selected jurisdiction’s configured requirements.', endpoint: '/compliance/check', kind: 'compliance', button: 'Check document' },
  'compliance-journey': { description: 'Build an evidence-linked compliance sequence from stored requirements and your document fields.', endpoint: '/compliance/journey', kind: 'journey', button: 'Build compliance journey' },
};

const initialValues = {
  question: '', title: '', description: '', ingredients: '', process: '', claimed_innovation: '', technical_advantage: '', therapeutic_use: '',
  language: 'en', intent: '', jurisdiction: 'IN', product_category: 'herbal_product', document_text: '', as_of: '', document_id: '',
};

type Values = typeof initialValues;

function AutoTextarea({ id, value, onChange, placeholder, required, rows = 4 }: { id: string; value: string; onChange: (value: string) => void; placeholder: string; required?: boolean; rows?: number }) {
  return <textarea id={id} value={value} rows={rows} placeholder={placeholder} required={required} onChange={(event) => onChange(event.target.value)} onInput={(event) => {
    const field = event.currentTarget;
    field.style.height = 'auto';
    field.style.height = `${field.scrollHeight}px`;
  }} />;
}

function EvidenceSafety({ page }: { page: ScreeningPageName }) {
  const copy = page === 'prior-art'
    ? 'An empty, failed or partial provider search cannot establish novelty. Inspect query counts, records and limitations.'
    : page === 'tk-risk'
      ? 'TKDL not connected and no authorized TK search means no final TK clearance. This screen remains preliminary.'
      : page === 'patentability'
        ? 'Readiness scores describe screening completeness. They are not a probability of patent grant.'
        : 'Every conclusion must remain tied to a source, its coverage and its limitations.';
  return <details className="source-safety"><summary><BookOpenCheck size={17} /> Evidence &amp; source safety <span>+</span></summary><div><strong>Read the evidence before the score.</strong><p>{copy}</p><Link href="/knowledge-library">Inspect the source library <ArrowUpRight size={14} /></Link></div></details>;
}

export default function ScreeningPage({ page }: { page: ScreeningPageName }) {
  const cfg = CONFIG[page];
  const [values, setValues] = useState<Values>(initialValues);
  const [countries, setCountries] = useState(['IN', 'US', 'EU', 'UK']);
  const [runPriorArt, setRunPriorArt] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [lastInput, setLastInput] = useState<Record<string, unknown> | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');
  const inventionFlow = page === 'patentability' || page === 'prior-art' || page === 'tk-risk';
  const complianceFlow = page === 'document-checker' || page === 'compliance-journey';
  const documents = useResource<DocumentsResponse>('/documents', complianceFlow);
  const reduceMotion = useReducedMotion();

  useEffect(() => {
    setValues((current) => ({
      ...current,
      language: localStorage.getItem('ip-sakti-language') || 'en',
      question: page === 'ask' ? new URLSearchParams(window.location.search).get('question') || '' : current.question,
    }));
  }, [page]);

  useEffect(() => {
    setSceneMetrics({
      jurisdictions: page === 'regulation-compare' ? countries : complianceFlow ? [values.jurisdiction] : [],
      documentSelected: complianceFlow && Boolean(values.document_id || values.document_text.trim()),
    });
  }, [complianceFlow, countries, page, values.document_id, values.document_text, values.jurisdiction]);

  useEffect(() => {
    if (!result) return;
    const routed = result?.routing?.primary ? result?.results?.[result.routing.primary] : null;
    const data = routed || result;
    const actualRecords = Array.isArray(data?.results) ? data.results : Array.isArray(data?.matches) ? data.matches : Array.isArray(data?.checks) ? data.checks : Array.isArray(data?.steps) ? data.steps : undefined;
    const citations = Array.isArray(result?.citations) ? result.citations : Array.isArray(data?.citations) ? data.citations : undefined;
    const similarity = Array.isArray(data?.results) && typeof data.results[0]?.similarity?.overall_similarity === 'number' ? data.results[0].similarity.overall_similarity : undefined;
    const readiness = typeof data?.assessment?.readiness?.score === 'number' ? data.assessment.readiness.score : similarity;
    const completedJourneySteps = page === 'compliance-journey' && Array.isArray(data?.steps)
      ? data.steps.filter((step: any) => ['complete', 'completed', 'done'].includes(String(step?.status || '').toLowerCase())).length
      : undefined;
    const tkRisk = page === 'tk-risk' ? String(data?.risk?.level || '') : '';
    setSceneMetrics({
      nodeCount: completedJourneySteps ?? actualRecords?.length ?? citations?.length,
      score: readiness,
      riskTone: tkRisk.startsWith('high_') ? 'high' : tkRisk.startsWith('moderate_') ? 'medium' : tkRisk.startsWith('low_') ? 'low' : undefined,
    });
  }, [page, result]);

  const set = (key: keyof Values, value: string) => { setValues((current) => ({ ...current, [key]: value })); if (!busy) setScenePhase(value ? 'input' : 'idle'); };

  const payload = useMemo(() => {
    if (page === 'ask') return { question: values.question, language: values.language, ...(values.intent ? { intent: values.intent } : {}) };
    if (page === 'regulation-compare') return { jurisdictions: countries, product_category: values.product_category, ...(values.as_of ? { as_of: values.as_of } : {}) };
    if (complianceFlow) return {
      jurisdiction: values.jurisdiction,
      product_category: values.product_category,
      document_text: values.document_text,
      ...(values.document_id ? { document_id: values.document_id } : {}),
      ...(values.as_of ? { as_of: values.as_of } : {}),
    };
    const common = {
      title: values.title,
      description: values.description,
      ingredients: values.ingredients.split(',').map((item) => item.trim()).filter(Boolean),
      process: values.process,
    };
    if (page === 'tk-risk') return { ...common, therapeutic_use: values.therapeutic_use };
    return {
      ...common,
      claimed_innovation: values.claimed_innovation,
      technical_advantage: values.technical_advantage,
      ...(page === 'patentability' ? { run_prior_art_search: runPriorArt } : { limit: 10 }),
    };
  }, [complianceFlow, countries, page, runPriorArt, values]);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (busy) return;
    setBusy(true); setError(''); setMessage(''); setResult(null); setScenePhase('submitting', page);
    try {
      setScenePhase('processing');
      const response = await api(cfg.endpoint, payload);
      setResult(response);
      setLastInput(payload);
      const isPartial = page === 'prior-art' && response?.search_summary?.search_status === 'partial';
      setScenePhase(isPartial ? 'partial' : 'success', isPartial ? 'partial-search' : 'complete');
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'The screening request could not be completed.');
      setScenePhase('error', 'request-error');
    } finally {
      setBusy(false);
    }
  };

  const save = async () => {
    if (!result || !lastInput || saving) return;
    setSaving(true); setMessage('');
    try {
      await api('/reports', {
        title: `${page.replaceAll('-', ' ')} report`,
        kind: cfg.kind,
        ...(result.assessment_id ? { assessment_id: result.assessment_id } : { input: lastInput }),
      });
      invalidateResource('/reports');
      setMessage('Report saved with its original evidence and limitations.');
      pulseScene('report-saved');
    } catch (reason) {
      setMessage(reason instanceof Error ? reason.message : 'The report could not be saved.');
    } finally {
      setSaving(false);
    }
  };

  const speak = async () => {
    setMessage('');
    try {
      const response: any = await api('/voice/synthesize', { text: result.answer, language: ['en', 'hi', 'mr'].includes(result.output_language) ? result.output_language : 'en' });
      if (response.audio_base64) await new Audio(`data:${response.mime_type};base64,${response.audio_base64}`).play();
      setMessage(response.message || response.status || 'Voice playback completed.');
    } catch (reason) {
      setMessage(reason instanceof Error ? reason.message : 'Voice playback is unavailable.');
    }
  };

  const field = (key: keyof Values, label: string, helper: string, placeholder: string, options: { required?: boolean; multiline?: boolean; rows?: number } = {}) => {
    const id = `${page}-${key}`;
    return <label className="form-field" htmlFor={id}><span>{label}{options.required && <b className="required"> *</b>}</span>
      {options.multiline ? <AutoTextarea id={id} value={values[key]} onChange={(value) => set(key, value)} placeholder={placeholder} required={options.required} rows={options.rows} /> : <input id={id} value={values[key]} onChange={(event) => set(key, event.target.value)} placeholder={placeholder} required={options.required} />}
      <small>{helper}</small>
    </label>;
  };

  const priorArtResult = result as PriorArtSearchResult | null;
  const partialSearch = page === 'prior-art' && priorArtResult?.search_summary?.search_status === 'partial';

  return <motion.div className="feature-page" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: reduceMotion ? 0 : .18 }}>
    <PageHeader page={page} description={cfg.description} />
    {page === 'ask' && <div className="ask-capabilities" aria-label="Question capabilities"><span><Search size={14} />Grounded search</span><span><BookOpenCheck size={14} />Citations</span><span><Mic size={14} />Voice upload</span><span><Sparkles size={14} />Responsible routing</span></div>}

    <section id="screening-form" className="panel screening-form-panel" aria-labelledby="form-title">
      <div className="section-title"><div><span className="eyebrow">INPUT / REVIEW</span><h2 id="form-title">{page === 'ask' ? 'Frame your research question' : complianceFlow ? 'Document and jurisdiction' : page === 'regulation-compare' ? 'Comparison scope' : 'Screening details'}</h2></div><span className="form-state"><i />Nothing runs until submitted</span></div>
      <form onSubmit={submit}>
        {page === 'ask' && <><ChatBox value={values.question} onChange={(value) => set('question', value)} language={values.language} /><div className="form-row"><label className="form-field"><span>Response language</span><select value={values.language} onChange={(event) => set('language', event.target.value)}><option value="en">English</option><option value="hi">हिन्दी</option><option value="mr">मराठी</option></select><small>Translation requires its separately configured provider.</small></label><label className="form-field"><span>Research route</span><select value={values.intent} onChange={(event) => set('intent', event.target.value)}><option value="">Detect intent</option><option value="ask">Grounded question answering</option><option value="patent">Patentability</option><option value="prior_art">Prior art</option><option value="traditional_knowledge">Traditional knowledge</option><option value="international">International regulation</option><option value="ayush">AYUSH</option><option value="compliance">Compliance</option></select><small>Automatic routing is used when no route is selected.</small></label></div></>}

        {inventionFlow && <div className="four-step-form">
          <fieldset><legend><span>01</span><b>Basic information</b><small>Identify what is being screened.</small></legend><div className="step-fields">{field('title', 'Invention or product title', 'Use a clear working name.', 'e.g., Standardized turmeric wound-care formulation', { required: page !== 'tk-risk' })}{field('description', 'Invention description', 'Describe formulation, function and technical context.', 'Describe the invention and intended use.', { required: true, multiline: true })}</div></fieldset>
          <fieldset><legend><span>02</span><b>Invention details</b><small>Record components and the claimed change.</small></legend><div className="step-fields">{field('ingredients', 'Ingredients or components', 'Separate entries with commas.', 'turmeric extract, aloe vera gel')}{page === 'tk-risk' ? field('therapeutic_use', 'Claimed therapeutic use', 'This records the claim; it does not verify efficacy.', 'Describe the claimed use.', { multiline: true }) : field('claimed_innovation', 'Claimed innovation', 'Explain the technical change or improvement.', 'What is new or different?', { multiline: true })}</div></fieldset>
          <fieldset><legend><span>03</span><b>Technical process</b><small>Add preparation steps and measurable advantages.</small></legend><div className="step-fields">{field('process', 'Preparation or manufacturing process', 'Use concrete steps where available.', 'Describe the actual process.', { multiline: true })}{page !== 'tk-risk' && field('technical_advantage', 'Technical advantage', 'Include measurements or supporting observations.', 'Describe the claimed technical effect.', { multiline: true })}</div></fieldset>
          <fieldset><legend><span>04</span><b>Review</b><small>Confirm scope before starting the backend request.</small></legend><div className="step-fields review-fields">{page === 'patentability' && <label className="checkbox-label"><input type="checkbox" checked={runPriorArt} onChange={(event) => setRunPriorArt(event.target.checked)} /><span><b>Include configured prior-art search</b><small>Provider coverage and limitations will be reported in the result.</small></span></label>}<p>This workflow produces a preliminary evidence screen. It does not provide legal advice, clearance or probability of grant.</p></div></fieldset>
        </div>}

        {page === 'regulation-compare' && <fieldset className="jurisdiction-fieldset"><legend>Jurisdictions</legend><p>Select one or more. Missing evidence is shown as missing, never as “no requirement.”</p><div className="country-options">{[['IN', 'India'], ['US', 'United States'], ['EU', 'European Union'], ['UK', 'United Kingdom']].map(([code, label]) => <label className={countries.includes(code) ? 'selected' : ''} key={code}><input type="checkbox" checked={countries.includes(code)} onChange={(event) => setCountries((current) => event.target.checked ? [...current, code] : current.filter((item) => item !== code))} /><span><strong>{code}</strong>{label}</span><Check size={16} /></label>)}</div></fieldset>}

        {(page === 'regulation-compare' || complianceFlow) && <div className="form-row">{complianceFlow && <label className="form-field"><span>Jurisdiction</span><select value={values.jurisdiction} onChange={(event) => set('jurisdiction', event.target.value)}><option value="IN">India</option><option value="US">United States</option><option value="EU">European Union</option><option value="UK">United Kingdom</option></select><small>Requirements come only from the configured source corpus.</small></label>}{field('product_category', 'Product category', 'Use a category represented by the configured corpus.', 'herbal_product', { required: true })}<label className="form-field"><span>Assessment date</span><input type="date" value={values.as_of} onChange={(event) => set('as_of', event.target.value)} /><small>Leave blank to use the currently applicable stored version.</small></label></div>}

        {complianceFlow && <div className="document-input-grid">{field('document_text', 'Pasted document text', 'Use explicit labels such as Product name, Ingredients and Manufacturer.', 'Product name: …\nIngredients: …\nManufacturer: …', { multiline: true, rows: 9 })}<label className="form-field"><span>Stored document</span><select value={values.document_id} onChange={(event) => set('document_id', event.target.value)}><option value="">No stored document selected</option>{documents.data?.documents.map((document) => <option value={document.id} key={document.id}>{document.name}</option>)}</select><small>{documents.error ? 'The document list is unavailable; pasted text remains supported.' : 'Upload and inspect source files in the Knowledge Library.'}</small></label><Link className="text-link" href="/knowledge-library">Open Knowledge Library <ArrowUpRight size={14} /></Link></div>}

        {!inventionFlow && <div className="form-actions"><small>Review the selected scope before starting this backend request.</small><button className="button primary" disabled={busy || (page === 'regulation-compare' && !countries.length)} type="submit">{busy ? <><LoaderCircle className="spin" size={16} />Processing…</> : <>{cfg.button}<ArrowUpRight size={16} /></>}</button></div>}
        {inventionFlow && <div className="form-actions"><small>Evidence and limitations will appear below when the request completes.</small><button className="button primary" disabled={busy} type="submit">{busy ? <><LoaderCircle className="spin" size={16} />Processing…</> : <>{cfg.button}<ArrowUpRight size={16} /></>}</button></div>}
      </form>
      {error && <ErrorState error={error} />}
    </section>

    <EvidenceSafety page={page} />
    {partialSearch && <Notice type="warning"><AlertTriangle size={18} /><div><strong>Partial patent search</strong><p>{priorArtResult.search_summary.queries_succeeded} of {priorArtResult.search_summary.queries_total} queries succeeded; {priorArtResult.search_summary.queries_failed} failed. Do not interpret returned records as complete coverage.</p></div></Notice>}
    {page === 'tk-risk' && result && result.tkdl_access !== true && result.authorized_search_performed !== true && <Notice type="warning"><ShieldAlert size={18} /><div><strong>TKDL Not Connected</strong><p>No authorized TK search was performed. This result cannot provide final TK clearance.</p></div></Notice>}

    {result && <section className="panel result-panel" aria-live="polite"><div className="result-toolbar"><div><span className="eyebrow">SCREENING OUTPUT</span><strong>Result and supporting evidence</strong></div><div className="inline-actions"><button className="button secondary small" type="button" onClick={save} disabled={saving}><Save size={15} />{saving ? 'Saving…' : 'Save report'}</button>{page === 'ask' && <button className="button ghost small" type="button" onClick={speak}><Headphones size={15} />Listen</button>}</div></div>{message && <Notice>{message} {message.startsWith('Report saved') && <Link href="/reports">Open reports <ArrowUpRight size={13} /></Link>}</Notice>}<ResultView result={result} /></section>}
    {!result && !busy && <section className="result-placeholder"><FileText size={22} /><div><strong>No assessment has run yet.</strong><p>Complete the form above. Results will preserve source coverage, evidence gaps and limitations.</p></div></section>}
  </motion.div>;
}
