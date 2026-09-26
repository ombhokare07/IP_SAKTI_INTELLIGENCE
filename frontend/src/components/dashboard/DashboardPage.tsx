'use client';

import { type FormEvent, useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { motion, useReducedMotion } from 'framer-motion';
import {
  ArrowUpRight,
  BookOpen,
  Database,
  FileCheck2,
  FileSearch,
  FileText,
  Globe2,
  Languages,
  Leaf,
  Mic2,
  Scale,
  Search,
  ShieldCheck,
  Sparkles,
} from 'lucide-react';
import { Empty } from '@/components/ResultView';
import { ErrorState, LoadingState, StatusBadge, formatLocalTime } from '@/components/ui/WorkspaceUI';
import { useResource } from '@/hooks/useResource';
import { authSessionStatus, countConnectedProviders, describeStatus } from '@/services/status.mjs';
import { describeMode } from '@/services/protocol.mjs';
import { setSceneHover, setSceneMetrics, setScenePhase } from '@/services/scene-signals.mjs';
import type { ReportsResponse, WorkspaceStatus } from '@/types/api';

const capabilities = [
  [ShieldCheck, 'Patents'],
  [Leaf, 'Traditional Knowledge'],
  [Scale, 'Regulations'],
  [Sparkles, 'Responsible AI'],
  [Languages, 'Multilingual'],
  [BookOpen, 'Evidence Grounded'],
] as const;

const quickActions = [
  { href: '/ask', title: 'Ask IP-SAKTI', copy: 'Start a grounded research question.', icon: Sparkles, tone: 'violet' },
  { href: '/patentability', title: 'Patentability', copy: 'Screen readiness and evidence gaps.', icon: FileCheck2, tone: 'indigo' },
  { href: '/prior-art', title: 'Prior Art', copy: 'Inspect configured patent records.', icon: FileSearch, tone: 'blue' },
  { href: '/tk-risk', title: 'TK Risk', copy: 'Review corpus scope and authorization.', icon: Leaf, tone: 'emerald' },
  { href: '/regulation-compare', title: 'Regulations', copy: 'Compare source-bound requirements.', icon: Scale, tone: 'cyan' },
] as const;

const journey = [
  ['01', 'Innovation', 'Frame the invention and intended use.'],
  ['02', 'Evidence', 'Inspect sources, coverage and gaps.'],
  ['03', 'Prior art', 'Review retrieved patent overlap.'],
  ['04', 'Traditional knowledge', 'Confirm authorization and corpus scope.'],
  ['05', 'Regulation', 'Compare applicable source requirements.'],
  ['06', 'Compliance', 'Prepare a traceable expert review.'],
] as const;

export default function DashboardPage() {
  const status = useResource<WorkspaceStatus>('/status');
  const reports = useResource<ReportsResponse>('/reports');
  const [question, setQuestion] = useState('');
  const router = useRouter();
  const reduceMotion = useReducedMotion();
  const providerMap = status.data?.providers || {};
  const providerTotal = Object.keys(providerMap).length;
  const connected = countConnectedProviders(providerMap);
  const chunks = status.data?.rag?.knowledge_base?.indexed_chunks;
  const reportItems = reports.data?.reports || [];
  const traditionalKnowledgeDetails = status.data?.provider_status?.traditional_knowledge;
  const tkdlConnected = typeof traditionalKnowledgeDetails === 'object' && traditionalKnowledgeDetails?.tkdl_connected === true;

  const submit = (event: FormEvent) => {
    event.preventDefault();
    if (question.trim()) { setScenePhase('submitting', 'question'); router.push(`/ask?question=${encodeURIComponent(question.trim())}`); }
  };

  useEffect(() => {
    setSceneMetrics({
      density: typeof chunks === 'number' ? chunks : undefined,
      nodeCount: status.data ? connected : undefined,
      providerTone: status.error ? 'unavailable' : providerTotal && connected === providerTotal ? 'ready' : connected ? 'partial' : 'neutral',
    });
  }, [chunks, connected, providerTotal, status.data, status.error]);

  const kpis = [
    { label: 'Indexed chunks', value: status.busy ? 'Checking…' : typeof chunks === 'number' ? String(chunks) : 'Unavailable', detail: 'Knowledge material reported by the backend.', icon: Database },
    { label: 'Verified providers', value: status.busy ? 'Checking…' : providerTotal ? `${connected} / ${providerTotal}` : 'Unavailable', detail: 'Excludes mock, unverified and authorization-required states.', icon: Globe2 },
    { label: 'Saved reports', value: reports.busy ? 'Checking…' : String(reportItems.length), detail: 'Traceable assessment snapshots returned by the backend.', icon: FileText },
    { label: 'RAG readiness', value: status.busy ? 'Checking…' : describeStatus(status.data?.rag).label, detail: 'Retrieval readiness reported by this workspace.', icon: BookOpen },
  ];

  const readiness = [
    ['Gemini', status.data?.rag?.gemini_readiness],
    ['RAG', status.data?.rag],
    ['EPO / prior art', status.data?.providers?.prior_art],
    ['Traditional knowledge', status.data?.providers?.traditional_knowledge],
    ['TKDL', tkdlConnected ? 'connected' : 'not_connected'],
    ['Regulations', status.data?.providers?.regulations],
    ['Translation', status.data?.providers?.translation],
    ['Speech to text', status.data?.providers?.speech_to_text],
    ['Text to speech', status.data?.providers?.text_to_speech],
    ['Google session', authSessionStatus(status.data)],
  ] as const;

  return <motion.div className="dashboard-page" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: reduceMotion ? 0 : .18 }}>
    <section className="dashboard-hero" aria-labelledby="dashboard-title">
      <div className="dashboard-hero__copy">
        <span className="eyebrow">AYUSH / EVIDENCE INTELLIGENCE</span>
        <h1 id="dashboard-title">IP-SAKTI <em>Intelligence</em></h1>
        <p>Evidence-grounded IP &amp; Regulatory Intelligence for AYUSH Innovation</p>
        <div className="capability-chips" aria-label="Workspace capabilities">
          {capabilities.map(([Icon, label]) => <span key={label} onPointerEnter={() => setSceneHover(label)} onPointerLeave={() => setSceneHover()}><Icon size={14} aria-hidden="true" />{label}</span>)}
        </div>
        <form className="hero-query" onSubmit={submit}>
          <label htmlFor="dashboard-question">What would you like to investigate?</label>
          <div><Search size={18} aria-hidden="true" /><input id="dashboard-question" value={question} onChange={(event) => { setQuestion(event.target.value); setScenePhase(event.target.value ? 'input' : 'idle'); }} placeholder="Ask about a formulation, claim, source or market…" required /><button className="button primary" type="submit">Investigate <ArrowUpRight size={16} /></button></div>
          <small>Searches run only after submission and retain their source scope and limitations.</small>
        </form>
      </div>
      <div className="dashboard-hero__visual" aria-hidden="true"><div className="hero-lattice"><i/><i/><i/><i/><i/><i/></div><div className="visual-caption"><span>Evidence network</span><strong>Trace claims to sources</strong></div></div>
    </section>

    {(status.error || reports.error) && <ErrorState error={[status.error, reports.error].filter(Boolean).join(' · ')} retry={status.error ? status.reload : reports.reload} />}

    <section className="kpi-grid" aria-label="Workspace metrics">
      {kpis.map(({ label, value, detail, icon: Icon }, index) => <motion.article className="kpi-card depth-card" key={label} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: reduceMotion ? 0 : .18, delay: reduceMotion ? 0 : index * .04 }}>
        <span className="kpi-card__icon"><Icon size={18} aria-hidden="true" /></span><div><span>{label}</span><strong>{value}</strong><p>{detail}</p></div>
      </motion.article>)}
    </section>

    <section className="dashboard-section" aria-labelledby="quick-actions-title">
      <div className="section-title"><div><span className="eyebrow">QUICK ACTIONS</span><h2 id="quick-actions-title">Start from the question that matters.</h2></div><p>Each workflow keeps evidence, limits and next steps together.</p></div>
      <div className="quick-action-grid">{quickActions.map(({ href, title, copy, icon: Icon, tone }) => <Link className={`quick-action depth-card ${tone}`} href={href} key={href} onPointerEnter={() => setSceneHover(title)} onPointerLeave={() => setSceneHover()}><span><Icon size={20} aria-hidden="true" /></span><div><strong>{title}</strong><small>{copy}</small></div><ArrowUpRight size={16} aria-hidden="true" /></Link>)}</div>
    </section>

    <div className="dashboard-detail-grid">
      <section className="panel readiness-panel depth-card"><div className="section-title"><div><span className="eyebrow">SYSTEM READINESS</span><h2>What is actually available</h2></div><Link href="/settings">Inspect settings <ArrowUpRight size={14} /></Link></div>
        {status.busy ? <LoadingState label="Checking provider readiness…" /> : <div className="readiness-list">{readiness.map(([label, value]) => <div key={label}><span>{label}</span><StatusBadge value={value} /></div>)}</div>}
        <p className="fine-print">A provider state describes availability only. It is not evidence, verification, legal clearance or a search result.</p>
      </section>
      <section className="panel recent-panel"><div className="section-title"><div><span className="eyebrow">RECENT ACTIVITY</span><h2>Saved investigations</h2></div><Link href="/reports">All reports <ArrowUpRight size={14} /></Link></div>
        {reports.busy ? <LoadingState label="Loading saved investigations…" /> : reportItems.length ? <div className="recent-report-list">{reportItems.slice(0, 5).map((report) => <Link href="/reports" key={report.id}><span><FileText size={15} /></span><div><strong>{report.title}</strong><small>{report.task || report.kind || 'Assessment'} · {describeMode(report.source_mode || report.mode)}</small></div><time>{formatLocalTime(report.created_at)}</time></Link>)}</div> : <Empty title="No recent activity">Saved assessments will appear here with their original evidence and source mode.</Empty>}
      </section>
    </div>

    <section className="panel journey-panel" aria-labelledby="journey-title"><div className="section-title"><div><span className="eyebrow">INNOVATION JOURNEY</span><h2 id="journey-title">From insight to responsible review.</h2></div></div><ol>{journey.map(([number, title, copy]) => <li key={number}><span>{number}</span><div><strong>{title}</strong><small>{copy}</small></div></li>)}</ol></section>
    <footer className="dashboard-signoff"><Leaf size={19} /><div><strong>Traditional Wisdom / Smarter Tomorrow.</strong><small>Responsible AI supports — and never replaces — human review.</small></div><Mic2 size={18} /></footer>
  </motion.div>;
}
