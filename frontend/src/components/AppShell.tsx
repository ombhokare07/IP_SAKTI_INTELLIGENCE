'use client';
import { useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { motion, useReducedMotion } from 'framer-motion';
import Sidebar from './Sidebar';
import Navbar from './Navbar';
import PersistentWorkspaceVisual, { sceneKeyForPath } from './three/PersistentWorkspaceVisual';
import DepthCardController from './ui/DepthCardController';
import { getResourceSnapshot, loadResource } from '@/services/resource-cache';
import type { AuthMeResponse } from '@/types/api';

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
  const [sessionError, setSessionError] = useState('');
  const [sessionNonce, setSessionNonce] = useState(0);
  const pathname = usePathname();
  const router = useRouter();
  const reduceMotion = useReducedMotion();
  const workspaceActive = pathname !== '/login';
  const scene = sceneKeyForPath(pathname);

  useEffect(() => {
    setSidebarCollapsed(localStorage.getItem('ip-sakti-sidebar-collapsed') === 'true');
  }, []);

  const toggleCollapsed = () => setSidebarCollapsed((current) => {
    const next = !current;
    localStorage.setItem('ip-sakti-sidebar-collapsed', String(next));
    return next;
  });

  useEffect(() => {
    if (!workspaceActive) {
      setCheckingSession(false);
      setSessionError('');
      return;
    }
    let active = true;
    const cached = getResourceSnapshot<AuthMeResponse>('/auth/me');
    if (cached.data?.authenticated && cached.data.user) {
      setUser(cached.data.user);
      setCheckingSession(false);
    } else if (!user) {
      setCheckingSession(true);
    }
    setSessionError('');
    loadResource<AuthMeResponse>('/auth/me', { force: sessionNonce > 0 })
      .then((data) => {
        if (!active) return;
        if (data?.authenticated && data.user) {
          setUser(data.user);
          setCheckingSession(false);
          return;
        }
        router.replace('/login');
      })
      .catch(() => {
        if (!active) return;
        setCheckingSession(false);
        if (!user) setSessionError('The secure workspace could not reach the backend. Your session has not been treated as signed out.');
      });
    return () => { active = false; };
  }, [router, sessionNonce, user, workspaceActive]);

  if (!workspaceActive) return <>{children}</>;

  if (sessionError) {
    return <main className="auth-loading auth-error" role="alert"><span/><p>{sessionError}</p><button className="button secondary" type="button" onClick={() => setSessionNonce((value) => value + 1)}>Retry connection</button></main>;
  }

  if (checkingSession && !user) {
    return <main className="auth-loading" aria-live="polite"><span/><p>Checking secure workspace access…</p></main>;
  }

  return (
    <div className={`app-shell scene-${scene}${sidebarCollapsed ? ' sidebar-collapsed' : ''}`} data-workspace-shell data-scene={scene}>
      <a className="skip-link" href="#main">Skip to content</a>
      <DepthCardController />
      <PersistentWorkspaceVisual />
      <Sidebar open={sidebarOpen} collapsed={sidebarCollapsed} onClose={()=>setSidebarOpen(false)} onToggleCollapsed={toggleCollapsed} />

      <div className="main-shell">
        <Navbar
          toggle={()=>setSidebarOpen(!sidebarOpen)}
          onToggleEvidence={()=>setEvidenceOpen((current)=>!current)}
          menuOpen={sidebarOpen}
          evidenceOpen={evidenceOpen}
          user={user}
        />

        <main id="main"><motion.div className="workspace-stage" key={pathname} initial={{opacity:0,y:6}} animate={{opacity:1,y:0}} transition={{duration:reduceMotion ? 0 : .18,ease:'easeOut'}}>{children}</motion.div></main>

        <footer className="workspace-footer">
          IP-SAKTI Intelligence <span>Screening scores are not legal conclusions or probabilities of patent grant.</span>
        </footer>
      </div>

      <EvidencePanel open={evidenceOpen} onClose={() => setEvidenceOpen(false)} />
    </div>
  );
}
