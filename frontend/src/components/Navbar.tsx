'use client';
import Link from 'next/link';
import { FormEvent, useEffect, useState } from 'react';
import { BellRing, BookOpenCheck, LogOut, Menu, Search } from 'lucide-react';
import { usePathname, useRouter } from 'next/navigation';
import { navigation } from './Sidebar';
import { API_BASE } from '@/services/api';
import type { SessionUser } from './AppShell';
import { summarizeProviders } from '@/services/status.mjs';
import { useResource } from '@/hooks/useResource';
import { clearResourceCache } from '@/services/resource-cache';
import type { WorkspaceStatus } from '@/types/api';

export default function Navbar({
  toggle,
  onToggleEvidence,
  menuOpen,
  evidenceOpen,
  user,
}: {
  toggle: () => void;
  onToggleEvidence: () => void;
  menuOpen: boolean;
  evidenceOpen: boolean;
  user: SessionUser | null;
}) {
  const pathname = usePathname();
  const router = useRouter();
  const current = navigation.find((n) => `/${n[0]}` === pathname)?.[1] || 'Dashboard';
  const [query, setQuery] = useState('');
  const [language, setLanguage] = useState('en');
  const status = useResource<WorkspaceStatus>('/status');
  const providerSummary = status.data ? summarizeProviders(status.data.providers) : null;
  const providerState: { tone: 'loading' | 'positive' | 'attention' | 'negative'; label: string } = status.error
    ? { tone: 'negative', label: 'Provider status unavailable' }
    : providerSummary
      ? { tone: providerSummary.tone as 'positive' | 'attention' | 'negative', label: providerSummary.label }
      : { tone: 'loading', label: 'Checking providers' };

  useEffect(() => {
    setLanguage(localStorage.getItem('ip-sakti-language') || 'en');
  }, []);

  const changeLanguage = (value: string) => {
    setLanguage(value);
    localStorage.setItem('ip-sakti-language', value);
  };

  const submit = (event: FormEvent) => {
    event.preventDefault();
    if (query.trim()) {
      router.push(`/ask?question=${encodeURIComponent(query.trim())}`);
    }
  };

  const logout = async () => {
    try {
      await fetch(`${API_BASE}/api/auth/logout`, {method:'POST', credentials:'include'});
    } finally {
      clearResourceCache();
      router.replace('/login');
      router.refresh();
    }
  };

  return (
    <header className="topbar">
      <button type="button" className="icon-button mobile-toggle" onClick={toggle} aria-label={menuOpen ? 'Close navigation' : 'Open navigation'} aria-expanded={menuOpen}>
        <Menu size={19} aria-hidden="true" />
      </button>

      <div className="breadcrumb">
        <span className="crumb-root">IP-SAKTI</span>
        <span className="crumb-separator">/</span>
        <strong>{current}</strong>
      </div>

      <form className="global-search" onSubmit={submit}>
        <Search size={17} aria-hidden="true" />
        <input
          aria-label="Search the workspace"
          suppressHydrationWarning
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search or ask a question..."
        />
      </form>

      <div className="top-actions">
        <label className="top-language">
          <span className="sr-only">Preferred response language</span>
          <select aria-label="Preferred response language" suppressHydrationWarning value={language} onChange={(event) => changeLanguage(event.target.value)}>
            <option value="en">EN</option><option value="hi">हि</option><option value="mr">म</option>
          </select>
        </label>
        <button type="button" className="evidence-toggle" onClick={onToggleEvidence} aria-label="Toggle evidence panel" aria-controls="evidence-panel" aria-expanded={evidenceOpen}>
          <BookOpenCheck className="evidence-toggle__icon" size={16} aria-hidden="true" />
          <span className="evidence-toggle__label">Evidence</span>
        </button>

        <Link href="/regulatory-alerts" className="alerts-action" aria-label="Open regulatory alerts"><BellRing size={17} aria-hidden="true"/><span className="sr-only">Regulatory alerts</span></Link>

        <span className={`provider-pulse ${providerState.tone}`}>
          <i />
          {providerState.label}
        </span>

        <Link href="/settings" className="profile-link" aria-label="Open settings">
          {user?.picture ? <img className="avatar avatar-image" src={user.picture} alt="" referrerPolicy="no-referrer" /> : <span className="avatar">{(user?.name || user?.email || '?').slice(0,2).toUpperCase()}</span>}
          <span>
            <b>{user?.name || user?.email || 'Verified user'}</b>
            <small>{user?.email || 'Authenticated session'}</small>
          </span>
          <em>⌄</em>
        </Link>
        <button type="button" className="logout-button" onClick={logout}><LogOut size={15} aria-hidden="true" /> <span>Logout</span></button>
      </div>
    </header>
  );
}
