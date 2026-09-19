'use client';
import { useState } from 'react';
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
        aria-label="Evidence panel"
        aria-hidden={false}
        aria-expanded={true}
        data-open={true}
      >
        <div className="evidence-panel__header">
          <div>
            <span className="eyebrow">EVIDENCE</span>
            <h2>Current case</h2>
          </div>
          <button type="button" className="panel-close" onClick={onClose} aria-label="Close evidence panel">✕</button>
        </div>

        <div className="evidence-panel__group">
          <div className="evidence-item">
            <span className="evidence-item__label">Source quality</span>
            <strong>High confidence</strong>
          </div>
          <div className="evidence-item">
            <span className="evidence-item__label">Open items</span>
            <strong>3 checks</strong>
          </div>
        </div>

        <div className="evidence-panel__list">
          <div className="evidence-row">
            <span className="dot dot--blue" />
            <div>
              <strong>Patentability</strong>
              <small>Claims and novelty review</small>
            </div>
          </div>
          <div className="evidence-row">
            <span className="dot dot--sage" />
            <div>
              <strong>Traditional knowledge</strong>
              <small>Community and prior use checks</small>
            </div>
          </div>
          <div className="evidence-row">
            <span className="dot dot--amber" />
            <div>
              <strong>Regulatory mapping</strong>
              <small>Jurisdiction-specific review</small>
            </div>
          </div>
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
