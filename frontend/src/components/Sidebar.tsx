'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useEffect, useRef } from 'react';
import {
  BellRing,
  BookOpen,
  ChartNoAxesCombined,
  CircleHelp,
  FileCheck2,
  FileClock,
  FileSearch,
  Gauge,
  Leaf,
  Library,
  PanelLeftClose,
  PanelLeftOpen,
  Route,
  Scale,
  Settings,
  ShieldCheck,
  X,
} from 'lucide-react';

export const navigation = [
  ['dashboard', 'Dashboard', Gauge],
  ['ask', 'Ask IP-SAKTI', CircleHelp],
  ['patentability', 'Patentability', ChartNoAxesCombined],
  ['prior-art', 'Prior Art', FileSearch],
  ['tk-risk', 'TK Risk', Leaf],
  ['regulation-compare', 'Regulation Compare', Scale],
  ['document-checker', 'Document Compliance', FileCheck2],
  ['regulation-changes', 'Regulation Changes', FileClock],
  ['compliance-journey', 'Compliance Journey', Route],
  ['knowledge-library', 'Knowledge Library', Library],
  ['regulatory-alerts', 'Regulatory Alerts', BellRing],
  ['reports', 'Reports', BookOpen],
  ['settings', 'Settings', Settings],
] as const;

const groups = [
  ['INTELLIGENCE', ['dashboard', 'ask']],
  ['IP ANALYSIS', ['patentability', 'prior-art', 'tk-risk']],
  ['REGULATION', ['regulation-compare', 'document-checker', 'regulation-changes', 'compliance-journey', 'regulatory-alerts']],
  ['WORKSPACE', ['knowledge-library', 'reports', 'settings']],
] as const;

export default function Sidebar({open, collapsed, onClose, onToggleCollapsed}: {open: boolean; collapsed: boolean; onClose: () => void; onToggleCollapsed: () => void}) {
  const path = usePathname();
  const sidebarRef = useRef<HTMLElement>(null);
  const isActive = (slug: string) => path === `/${slug}` || (path === '/' && slug === 'dashboard');

  useEffect(() => {
    if (!open) return;
    const previous = document.activeElement as HTMLElement | null;
    const close = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose();
      if (event.key === 'Tab' && sidebarRef.current) {
        const focusable = [...sidebarRef.current.querySelectorAll<HTMLElement>('a, button:not([disabled])')];
        if (!focusable.length) return;
        const first = focusable[0];
        const last = focusable[focusable.length - 1];
        if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
        else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
      }
    };
    document.addEventListener('keydown', close);
    document.body.style.overflow = 'hidden';
    window.requestAnimationFrame(() => sidebarRef.current?.querySelector<HTMLElement>('a, button')?.focus());
    return () => { document.removeEventListener('keydown', close); document.body.style.overflow = ''; previous?.focus(); };
  }, [open, onClose]);

  return <>
    {open && <button className="nav-scrim visible" aria-label="Close navigation" onClick={onClose}/>}
    <aside ref={sidebarRef} className={`sidebar ${open ? 'open' : ''}${collapsed ? ' collapsed' : ''}`} aria-label="Workspace navigation">
      <div className="sidebar-head">
        <Link href="/dashboard" className="brand" onClick={onClose}>
          <span className="brand-mark"><Leaf size={18}/></span>
          <span>IP-SAKTI<small>Intelligence workspace</small></span>
        </Link>
        <button type="button" className="sidebar-close" onClick={onClose} aria-label="Close navigation"><X size={19}/></button>
        <button type="button" className="sidebar-collapse" onClick={onToggleCollapsed} aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'} aria-pressed={collapsed}>{collapsed ? <PanelLeftOpen size={18}/> : <PanelLeftClose size={18}/>}</button>
      </div>
      <nav aria-label="Main navigation">
        {groups.map(([group, slugs]) => <section className="nav-group" key={group}>
          <div className="nav-label">{group}</div>
          {slugs.map((slug) => {
            const item = navigation.find((entry) => entry[0] === slug)!;
            const Icon = item[2];
            return <Link key={slug} href={`/${slug}`} onClick={onClose} aria-current={isActive(slug) ? 'page' : undefined} className={isActive(slug) ? 'active' : ''} title={item[1]}>
              <span className="nav-symbol" aria-hidden="true"><Icon size={17}/></span>
              <span>{item[1]}</span>
            </Link>;
          })}
        </section>)}
      </nav>
      <div className="sidebar-foot"><span className="shield-icon"><ShieldCheck size={16}/></span><div><strong>Traditional Wisdom</strong><small>Smarter Tomorrow.</small></div></div>
    </aside>
  </>;
}
