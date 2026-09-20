'use client';
import { useState } from 'react';
import Link from 'next/link';
import Sidebar from './Sidebar';
import Navbar from './Navbar';

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

  return (
    <div className="app-shell">
      <a className="skip-link" href="#main">Skip to content</a>
      <Sidebar open={sidebarOpen} onClose={()=>setSidebarOpen(false)} />

      <div className="main-shell">
        <Navbar
          toggle={()=>setSidebarOpen(!sidebarOpen)}
          onToggleEvidence={()=>setEvidenceOpen((current)=>!current)}
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
