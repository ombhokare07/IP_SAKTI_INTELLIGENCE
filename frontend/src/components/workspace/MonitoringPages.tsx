'use client';

import { useEffect, useState } from 'react';
import { AlertCircle, BellRing, CalendarClock, CheckCheck, RefreshCw } from 'lucide-react';
import { Empty, Notice } from '@/components/ResultView';
import { ErrorState, LoadingState, PageHeader, formatLocalTime } from '@/components/ui/WorkspaceUI';
import { useResource } from '@/hooks/useResource';
import { api } from '@/services/api';
import { describeMode } from '@/services/protocol.mjs';
import { pulseScene, setSceneMetrics, setScenePhase } from '@/services/scene-signals.mjs';

export function RegulationChangesPage() {
  const resource = useResource<any>('/regulations/changes');
  const [syncing, setSyncing] = useState(false);
  const [message, setMessage] = useState('');

  const synchronize = async () => {
    setSyncing(true); setMessage(''); setScenePhase('processing');
    try {
      const response: any = await api('/regulations/sync', {});
      setMessage(`${String(response.status).replaceAll('_', ' ')} · ${response.imported || 0} versions imported.`);
      resource.reload();
      setScenePhase('success', 'regulation-sync');
    } catch (reason) {
      setMessage(reason instanceof Error ? reason.message : 'Synchronization could not be completed.');
      setScenePhase('error', 'sync-error');
    } finally { setSyncing(false); }
  };

  const changes = resource.data?.changes || [];
  useEffect(() => { setSceneMetrics({ nodeCount: changes.length }); }, [changes.length]);
  return <div className="workspace-page changes-page">
    <PageHeader page="regulation-changes" description="Review backend-stored differences between regulatory source versions; no continuous live feed is implied." action={<button className="button primary" type="button" disabled={syncing} onClick={synchronize}><RefreshCw className={syncing ? 'spin' : ''} size={15} />{syncing ? 'Synchronizing…' : 'Synchronize source'}</button>} />
    {message && <Notice>{message}</Notice>}
    {resource.busy ? <LoadingState label="Loading stored regulatory changes…" /> : resource.error ? <ErrorState error={resource.error} retry={resource.reload} /> : <>
      <Notice><CalendarClock size={17} /><div><strong>{describeMode(resource.data?.mode)}</strong><p>Last successful synchronization: {resource.data?.sync?.last_success ? formatLocalTime(resource.data.sync.last_success) : 'None reported'}.</p></div></Notice>
      {!changes.length ? <section className="panel"><Empty title="No stored changes to compare">Configure and synchronize a versioned regulatory source. No stored changes does not mean regulations have not changed.</Empty></section> : <ol className="change-timeline">{changes.map((change: any, index: number) => <li key={`${change.regulation_id || 'change'}-${index}`}><span className="timeline-marker"><CalendarClock size={16} /></span><article className="panel change-card depth-card"><div className="row-between"><span className="eyebrow">{change.jurisdiction} · {change.regulation_id}</span><span className={`badge ${change.mode === 'mock' ? 'warning' : ''}`}>{describeMode(change.mode)}</span></div><h2>{change.from_version} <span className="muted">→</span> {change.to_version}</h2><p>Stored effective date: {change.effective_from || 'Not reported'}</p><div className="change-stats"><span><strong>{change.added?.length || 0}</strong>Added</span><span><strong>{change.changed?.length || 0}</strong>Changed</span><span><strong>{change.removed?.length || 0}</strong>Removed</span></div>{change.impact?.affected_fields?.length > 0 && <><h3>Fields to review</h3><div className="chips">{change.impact.affected_fields.map((field: string) => <span className="chip" key={field}>{field.replaceAll('_', ' ')}</span>)}</div></>}{change.impact?.actions?.length > 0 && <ul className="checklist">{change.impact.actions.map((action: string) => <li key={action}>{action}</li>)}</ul>}<details><summary>Source text diff</summary><pre>{change.text_diff || 'No source text change supplied.'}</pre></details><details><summary>Requirement and provenance detail</summary><pre>{JSON.stringify(change, null, 2)}</pre></details></article></li>)}</ol>}
    </>}
  </div>;
}

export function RegulatoryAlertsPage() {
  const resource = useResource<any>('/alerts');
  const [message, setMessage] = useState('');
  const [acknowledging, setAcknowledging] = useState('');
  const alerts = resource.data?.alerts || [];
  useEffect(() => { setSceneMetrics({ nodeCount: alerts.length }); }, [alerts.length]);

  const acknowledge = async (id: string) => {
    setAcknowledging(id); setMessage('');
    try { await api(`/alerts/${id}/acknowledge`, {}); resource.reload(); pulseScene('alert-reviewed'); }
    catch (reason) { setMessage(reason instanceof Error ? reason.message : 'The alert could not be acknowledged.'); }
    finally { setAcknowledging(''); }
  };

  return <div className="workspace-page alerts-page">
    <PageHeader page="regulatory-alerts" description="Review in-app alerts derived from synchronized regulation versions. No external notification delivery is implied." />
    {message && <Notice type="error"><AlertCircle size={17} />{message}</Notice>}
    {resource.busy ? <LoadingState label="Loading regulatory alerts…" /> : resource.error ? <ErrorState error={resource.error} retry={resource.reload} /> : !alerts.length ? <section className="panel"><Empty title="No stored alerts">Alerts appear when synchronized snapshots contain backend-reported changes. No alert does not mean no regulation has changed.</Empty></section> : <section className="alert-grid">{alerts.map((alert: any) => <article className={`alert-card depth-card${alert.acknowledged ? ' acknowledged' : ''}`} key={alert.id}><header><span><BellRing size={18} /></span><div><span className={`badge ${alert.mode === 'mock' ? 'warning' : ''}`}>{describeMode(alert.mode)}</span><h2>{alert.title}</h2></div></header><dl><div><dt>Jurisdiction</dt><dd>{alert.jurisdiction}</dd></div><div><dt>Effective date</dt><dd>{alert.effective_from || 'Not reported'}</dd></div><div><dt>Review priority</dt><dd>{alert.impact?.review_priority || 'Not reported'}</dd></div></dl>{alert.impact?.affected_fields?.length > 0 && <div className="chips">{alert.impact.affected_fields.map((field: string) => <span className="chip" key={field}>{field.replaceAll('_', ' ')}</span>)}</div>}<button className="button secondary small" type="button" disabled={alert.acknowledged || acknowledging === alert.id} onClick={() => acknowledge(alert.id)}><CheckCheck size={15} />{alert.acknowledged ? 'Reviewed' : acknowledging === alert.id ? 'Saving…' : 'Mark reviewed'}</button></article>)}</section>}
  </div>;
}
