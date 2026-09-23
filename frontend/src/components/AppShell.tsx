'use client';
import { useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { motion, useReducedMotion } from 'framer-motion';
import Sidebar from './Sidebar';
import Navbar from './Navbar';
import { API_BASE } from '@/services/api';

export type SessionUser = {email:string;name:string;picture:string};

function EvidencePanel({open, onClose}:{open:boolean; onClose:()=>void}) {
  const closeRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!open) return;
    const previous = document.activeElement as HTMLElement | null;
    const close = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose();
      if (event.key === 'Tab') {
        const panel = closeRef.current?.closest<HTMLElement>('[role="dialog"]');
        const focusable = panel ? [...panel.querySelectorAll<HTMLElement>('a, button:not([disabled])')] : [];
        if (!focusable.length) return;
        const first = focusable[0];
        const last = focusable[focusable.length - 1];
        if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
        else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
      }
    };
    document.addEventListener('keydown', close);
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    closeRef.current?.focus();
    return () => {
      document.removeEventListener('keydown', close);
      document.body.style.overflow = previousOverflow;
      previous?.focus();
    };
  }, [open, onClose]);

  if (!open) return null;

  return (
    <>
      <button type="button" className="evidence-scrim" onClick={onClose} aria-label="Close evidence panel" />
      <aside
        id="evidence-panel"
        className="evidence-panel open"
        aria-label="Evidence review guide"
        role="dialog"
        aria-modal="true"
      >
        <div className="evidence-panel__header">
          <div>
            <span className="eyebrow">REVIEW GUIDE</span>
            <h2>Read a screening safely</h2>
          </div>
          <button ref={closeRef} type="button" className="panel-close" onClick={onClose} aria-label="Close evidence panel">✕</button>
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
  const [sidebarCollapsed, setSidebarCollapsed] = useState<boolean>(false);
  const [evidenceOpen, setEvidenceOpen] = useState<boolean>(false);
  const [user, setUser] = useState<SessionUser|null>(null);
  const [checkingSession, setCheckingSession] = useState(true);
  const [authorizedPath, setAuthorizedPath] = useState<string|null>(null);
  const [sessionError, setSessionError] = useState('');
  const [sessionNonce, setSessionNonce] = useState(0);
  const pathname = usePathname();
  const router = useRouter();
  const reduceMotion = useReducedMotion();

  useEffect(() => {
    setSidebarCollapsed(localStorage.getItem('ip-sakti-sidebar-collapsed') === 'true');
  }, []);

  const toggleCollapsed = () => setSidebarCollapsed((current) => {
    const next = !current;
    localStorage.setItem('ip-sakti-sidebar-collapsed', String(next));
    return next;
  });

  useEffect(() => {
    if (pathname === '/login') {
      setCheckingSession(false);
      setAuthorizedPath(pathname);
      return;
    }
    let active = true;
    setCheckingSession(true);
    setAuthorizedPath(null);
    setSessionError('');
    fetch(`${API_BASE}/api/auth/me`, {credentials:'include'})
      .then(async (response) => {
        if (!response.ok) throw new Error(`Session check failed with HTTP ${response.status}.`);
        return response.json();
      })
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
      .catch(() => {
        if (!active) return;
        setCheckingSession(false);
        setSessionError('The secure workspace could not reach the backend. Your session has not been treated as signed out.');
      });
    return () => { active = false; };
  }, [pathname, router, sessionNonce]);

  if (pathname === '/login') return <>{children}</>;

  if (sessionError) {
    return <main className="auth-loading auth-error" role="alert"><span/><p>{sessionError}</p><button className="button secondary" type="button" onClick={() => setSessionNonce((value) => value + 1)}>Retry connection</button></main>;
  }

  if (checkingSession || authorizedPath !== pathname) {
    return <main className="auth-loading" aria-live="polite"><span/><p>Checking secure workspace access…</p></main>;
  }

  return (
    <div className={`app-shell${sidebarCollapsed ? ' sidebar-collapsed' : ''}`}>
      <a className="skip-link" href="#main">Skip to content</a>
      <Sidebar open={sidebarOpen} collapsed={sidebarCollapsed} onClose={()=>setSidebarOpen(false)} onToggleCollapsed={toggleCollapsed} />

      <div className="main-shell">
        <Navbar
          toggle={()=>setSidebarOpen(!sidebarOpen)}
          onToggleEvidence={()=>setEvidenceOpen((current)=>!current)}
          menuOpen={sidebarOpen}
          evidenceOpen={evidenceOpen}
          user={user}
        />

        <main id="main"><motion.div className="workspace-stage" key={pathname} initial={reduceMotion ? false : {opacity:0,y:8}} animate={{opacity:1,y:0}} transition={{duration:.24,ease:'easeOut'}}>{children}</motion.div></main>

        <footer className="workspace-footer">
          IP-SAKTI Intelligence <span>Screening scores are not legal conclusions or probabilities of patent grant.</span>
        </footer>
      </div>

      <EvidencePanel open={evidenceOpen} onClose={() => setEvidenceOpen(false)} />
    </div>
  );
}
