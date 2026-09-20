'use client';
import { useEffect, useState } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import Sidebar from './Sidebar';
import Navbar from './Navbar';
import { API_BASE } from '@/services/api';

export type SessionUser = {email:string;name:string;picture:string};

function EvidencePanel({open, onClose}:{open:boolean; onClose:()=>void}) {
  if (!open) return null;

  return (
    <>
      <button type="button" className="evidence-scrim" onClick={onClose} aria-label="Close evidence panel" />
      <aside
        id="evidence-panel"
        className="evidence-panel open"
        aria-label="Evidence review guide"
        aria-hidden={false}
        aria-expanded={true}
        data-open={true}
      >
        <div className="evidence-panel__header">
          <div>
            <span className="eyebrow">REVIEW GUIDE</span>
            <h2>Read a screening safely</h2>
          </div>
          <button type="button" className="panel-close" onClick={onClose} aria-label="Close evidence panel">✕</button>
        </div>

        <p className="evidence-panel__intro">Each result separates what was searched, what remains unassessed and which source excerpts support the screen.</p>

        <div className="evidence-panel__list">
          <div className="evidence-row">
            <span className="dot dot--blue" />
            <div>
              <strong>Start with the summary</strong>
              <small>Confirm provider, search and authorization status.</small>
            </div>
          </div>
          <div className="evidence-row">
            <span className="dot dot--sage" />
            <div>
              <strong>Inspect supporting sources</strong>
              <small>Open excerpts and verify the underlying record.</small>
            </div>
          </div>
          <div className="evidence-row">
            <span className="dot dot--amber" />
            <div>
              <strong>Resolve important gaps</strong>
              <small>Unsearched or missing evidence is never a clearance.</small>
            </div>
          </div>
        </div>
        <div className="evidence-panel__actions">
          <Link className="button primary small" href="/knowledge-library" onClick={onClose}>Open source library</Link>
          <Link className="button ghost small" href="/settings" onClick={onClose}>Check provider status</Link>
        </div>
      </aside>
    </>
  );
}

export default function AppShell({children}:{children:React.ReactNode}) {
  const [sidebarOpen, setSidebarOpen] = useState<boolean>(false);
  const [evidenceOpen, setEvidenceOpen] = useState<boolean>(false);
  const [user, setUser] = useState<SessionUser|null>(null);
  const [checkingSession, setCheckingSession] = useState(true);
  const [authorizedPath, setAuthorizedPath] = useState<string|null>(null);
  const pathname = usePathname();
  const router = useRouter();

  useEffect(() => {
    if (pathname === '/login') {
      setCheckingSession(false);
      setAuthorizedPath(pathname);
      return;
    }
    let active = true;
    setCheckingSession(true);
    setAuthorizedPath(null);
    fetch(`${API_BASE}/api/auth/me`, {credentials:'include'})
      .then(async (response) => response.ok ? response.json() : {authenticated:false})
      .then((data) => {
        if (!active) return;
        if (data?.authenticated && data.user) {
          setUser(data.user);
          setCheckingSession(false);
          setAuthorizedPath(pathname);
          return;
        }
        router.replace('/login');
      })
      .catch(() => active && router.replace('/login'));
    return () => { active = false; };
  }, [pathname, router]);

  if (pathname === '/login') return <>{children}</>;

  if (checkingSession || authorizedPath !== pathname) {
    return <main className="auth-loading" aria-live="polite"><span/><p>Checking secure workspace access…</p></main>;
  }

  return (
    <div className="app-shell">
      <a className="skip-link" href="#main">Skip to content</a>
      <Sidebar open={sidebarOpen} onClose={()=>setSidebarOpen(false)} />

      <div className="main-shell">
        <Navbar
          toggle={()=>setSidebarOpen(!sidebarOpen)}
          onToggleEvidence={()=>setEvidenceOpen((current)=>!current)}
          user={user}
        />

        <main id="main">{children}</main>

        <footer className="workspace-footer">
          IP-SAKTI Intelligence <span>Screening scores are not legal conclusions or probabilities of patent grant.</span>
        </footer>
      </div>

      <EvidencePanel open={evidenceOpen} onClose={() => setEvidenceOpen(false)} />
    </div>
  );
}
