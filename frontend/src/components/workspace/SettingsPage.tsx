'use client';

import { type FormEvent, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Database, Globe2, Languages, LogOut, Mic2, Save, ShieldCheck, Volume2 } from 'lucide-react';
import { Notice } from '@/components/ResultView';
import { ErrorState, LoadingState, PageHeader, StatusBadge } from '@/components/ui/WorkspaceUI';
import { useResource } from '@/hooks/useResource';
import { API_BASE } from '@/services/api';
import { authSessionStatus } from '@/services/status.mjs';
import type { AuthMeResponse, ProviderStatusValue, WorkspaceStatus } from '@/types/api';

function SettingRow({ label, value, detail }: { label: string; value: ProviderStatusValue; detail: string }) {
  return <div className="setting-row"><div><strong>{label}</strong><small>{detail}</small></div><StatusBadge value={value} /></div>;
}

export default function SettingsPage() {
  const status = useResource<WorkspaceStatus>('/status');
  const session = useResource<AuthMeResponse>('/auth/me');
  const [language, setLanguage] = useState('en');
  const [message, setMessage] = useState('');
  const router = useRouter();

  useEffect(() => setLanguage(localStorage.getItem('ip-sakti-language') || 'en'), []);

  const save = (event: FormEvent) => {
    event.preventDefault();
    localStorage.setItem('ip-sakti-language', language);
    setMessage('Language preference saved for this browser.');
  };

  const logout = async () => {
    try { await fetch(`${API_BASE}/api/auth/logout`, { method: 'POST', credentials: 'include' }); }
    finally { router.replace('/login'); router.refresh(); }
  };

  const data = status.data;
  const providerStatus = data?.provider_status || {};
  const tkDetails = providerStatus.traditional_knowledge && typeof providerStatus.traditional_knowledge === 'object' ? providerStatus.traditional_knowledge : {};
  const auth = data?.authentication;
  const googleSession = authSessionStatus(data);
  const account = session.data?.user;

  return <div className="workspace-page settings-page">
    <PageHeader page="settings" description="Inspect exact backend readiness, evidence connectors, language and voice capabilities, and your authenticated Google session." />
    {message && <Notice>{message}</Notice>}
    {status.error && <ErrorState error={status.error} retry={status.reload} />}
    {status.busy ? <LoadingState label="Checking workspace configuration…" /> : <div className="settings-grid">
      <section className="panel settings-group"><header><span><Database size={18} /></span><div><span className="eyebrow">AI &amp; KNOWLEDGE</span><h2>Grounding readiness</h2></div></header>
        <SettingRow label="Gemini" value={data?.rag?.gemini_readiness} detail="Model readiness reported by the backend pipeline." />
        <SettingRow label="RAG workspace" value={data?.rag} detail="Ready only when the retrieval pipeline and index are usable." />
        <SettingRow label="Embeddings" value={data?.rag?.embeddings} detail={`Model: ${data?.rag?.embeddings?.model || 'not reported'}.`} />
        <SettingRow label="Vector store" value={data?.rag?.vector_store_readiness} detail="Local vector-store initialization state." />
        <SettingRow label="Knowledge base" value={data?.rag?.knowledge_base} detail={`${data?.rag?.knowledge_base?.indexed_chunks ?? 0} indexed chunks reported.`} />
      </section>

      <section className="panel settings-group"><header><span><Globe2 size={18} /></span><div><span className="eyebrow">EVIDENCE CONNECTORS</span><h2>Research sources</h2></div></header>
        <SettingRow label="Patent / EPO search" value={data?.providers?.prior_art} detail="Configured access remains unverified until a successful provider request." />
        <SettingRow label="Traditional knowledge" value={data?.providers?.traditional_knowledge} detail={tkDetails.authorized === true ? 'Backend reports an authorized configured provider.' : 'Authorization has not been reported; no final TK clearance is possible.'} />
        <SettingRow label="TKDL" value={tkDetails.tkdl_connected === true ? 'connected' : 'not_connected'} detail={tkDetails.tkdl_connected === true ? 'The backend reports a TKDL connection.' : 'TKDL Not Connected. No bundled TKDL integration is implied.'} />
        <SettingRow label="Regulation corpus" value={data?.providers?.regulations} detail="Comparisons use only the configured, versioned source corpus." />
      </section>

      <section className="panel settings-group"><header><span><Languages size={18} /></span><div><span className="eyebrow">LANGUAGE &amp; VOICE</span><h2>Optional capabilities</h2></div></header>
        <SettingRow label="Translation" value={data?.providers?.translation} detail={`Execution: ${(providerStatus.translation as any)?.execution || 'not reported'}. Original text remains available.`} />
        <SettingRow label="Speech to text" value={data?.providers?.speech_to_text} detail={`Execution: ${(providerStatus.speech_to_text as any)?.execution || 'not reported'}. Typed input remains available.`} />
        <SettingRow label="Text to speech" value={data?.providers?.text_to_speech} detail={`${(providerStatus.text_to_speech as any)?.requires_internet ? 'Internet is required. ' : ''}Execution: ${(providerStatus.text_to_speech as any)?.execution || 'not reported'}.`} />
        <form className="preference-form" onSubmit={save}><label className="form-field"><span>Preferred response language</span><select value={language} onChange={(event) => setLanguage(event.target.value)}><option value="en">English</option><option value="hi">हिन्दी</option><option value="mr">मराठी</option></select><small>Saved locally in this browser; it does not configure a backend provider.</small></label><button className="button primary" type="submit"><Save size={15} />Save preference</button></form>
      </section>

      <section className="panel settings-group security-group"><header><span><ShieldCheck size={18} /></span><div><span className="eyebrow">SECURITY</span><h2>Google session</h2></div></header>
        <SettingRow label="Google sign-in + session cookie" value={googleSession.connected ? 'connected' : 'not_configured'} detail="Normal user access uses a verified Google identity and secure HttpOnly application session." />
        <SettingRow label="Google sign-in backend" value={auth?.google_sign_in} detail="Configuration state only; it does not expose any credential." />
        <SettingRow label="Session cookie backend" value={auth?.session_cookie} detail="Configuration state for the signed application session." />
        <div className="session-card"><span className="avatar">{(account?.name || account?.email || '?').slice(0, 2).toUpperCase()}</span><div><strong>{account?.name || 'Authenticated user'}</strong><small>{account?.email || (session.busy ? 'Checking current session…' : 'Session details unavailable')}</small>{account?.account?.created_at && <small>Workspace account created {new Date(account.account.created_at).toLocaleDateString()}</small>}</div></div>
        <button className="button secondary" type="button" onClick={logout}><LogOut size={15} />Sign out</button>
      </section>
    </div>}
    <details className="panel settings-advanced"><summary>Advanced deployment notes</summary><div className="settings-notes"><div><h3>Provider credentials</h3><p>Configure provider credentials only in the backend environment. This normal-user screen never accepts or displays API tokens.</p></div><div><h3>Traditional knowledge</h3><p>Use only an authorized local corpus or compatible gateway. A configured provider and TKDL connection are separate states.</p></div><div><h3>Local and online voice</h3><p><Mic2 size={14} /> Speech recognition may execute locally; <Volume2 size={14} /> synthesis can still require internet. The exact status above comes from the backend.</p></div></div><p className="fine-print">Backend address: <code>{API_BASE}</code>. Restart the backend after deployment environment changes.</p></details>
  </div>;
}
