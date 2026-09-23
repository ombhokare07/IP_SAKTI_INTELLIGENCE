'use client';

import { useState } from 'react';
import { ArrowDownToLine, FileJson, FileText, Printer, X } from 'lucide-react';
import ResultView, { Empty, Notice } from '@/components/ResultView';
import { ErrorState, LoadingState, PageHeader, formatLocalTime } from '@/components/ui/WorkspaceUI';
import { useResource } from '@/hooks/useResource';
import { api, download } from '@/services/api';
import { describeMode } from '@/services/protocol.mjs';
import type { ReportsResponse } from '@/types/api';

export default function ReportsPage() {
  const resource = useResource<ReportsResponse>('/reports');
  const [selected, setSelected] = useState<any>(null);
  const [opening, setOpening] = useState('');
  const [message, setMessage] = useState('');
  const reports = resource.data?.reports || [];

  const open = async (id: string) => {
    setOpening(id); setMessage('');
    try { setSelected(await api(`/reports/${id}`)); }
    catch (reason) { setMessage(reason instanceof Error ? reason.message : 'The report could not be opened.'); }
    finally { setOpening(''); }
  };

  const exportReport = (format: string, suffix: string) => {
    if (!selected) return;
    download(`/reports/${selected.id}/export?format=${format}`, `IP-SAKTI-${selected.id}.${suffix}`).catch((reason) => setMessage(reason.message));
  };

  return <div className="workspace-page reports-page">
    <PageHeader page="reports" description="Open and export saved assessments with their original evidence, source mode and limitations." />
    {message && <Notice>{message}</Notice>}
    {resource.busy ? <LoadingState label="Loading saved reports…" /> : resource.error ? <ErrorState error={resource.error} retry={resource.reload} /> : <section className="panel report-panel">{reports.length ? <div className="table-scroll"><table className="report-table"><thead><tr><th>Report</th><th>Task</th><th>Evidence mode</th><th>Created</th><th>Status</th><th>Action</th></tr></thead><tbody>{reports.map((report) => <tr key={report.id}><th><FileText size={15} /><span>{report.title}<small>Saved assessment</small></span></th><td>{report.task || String(report.kind || 'assessment').replaceAll('_', ' ')}</td><td><span className={`badge ${(report.source_mode || report.mode) === 'mock' || (report.source_mode || report.mode) === 'synthetic' ? 'warning' : ''}`}>{describeMode(report.source_mode || report.mode)}</span></td><td>{formatLocalTime(report.created_at)}</td><td>{String(report.status || 'saved').replaceAll('_', ' ')}</td><td><button className="button secondary small" type="button" disabled={opening === report.id} onClick={() => open(report.id)}>{opening === report.id ? 'Opening…' : 'Open report'}</button></td></tr>)}</tbody></table></div> : <Empty title="No saved reports yet">Run a screening and save the assessment to retain its source context.</Empty>}</section>}

    {selected && <section className="panel opened-report"><header><div><span className="eyebrow">SAVED ASSESSMENT</span><h2>{selected.title}</h2></div><button className="panel-close" type="button" onClick={() => setSelected(null)} aria-label="Close report"><X size={17} /></button></header><div className="export-bar" aria-label="Report exports"><span>Export complete assessment</span><button className="button secondary small" type="button" onClick={() => exportReport('json', 'json')}><FileJson size={15} />JSON</button><button className="button secondary small" type="button" onClick={() => exportReport('markdown', 'md')}><ArrowDownToLine size={15} />Markdown</button><button className="button secondary small" type="button" onClick={() => exportReport('html', 'html')}><Printer size={15} />Printable HTML</button></div><p className="fine-print">HTML exports can be printed to PDF from the browser. Exports retain citations and limitations.</p><ResultView result={selected.assessment} /></section>}
  </div>;
}
