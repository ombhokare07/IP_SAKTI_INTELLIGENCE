'use client';
import Link from 'next/link';
import { FormEvent, useEffect, useState } from 'react';
import { Bell, Menu, Search } from 'lucide-react';
import { usePathname, useRouter } from 'next/navigation';
import { navigation } from './Sidebar';
import { api } from '@/services/api';

export default function Navbar({
  toggle,
  onToggleEvidence,
}: {
  toggle: () => void;
  onToggleEvidence: () => void;
}) {
  const pathname = usePathname();
  const router = useRouter();
  const current = navigation.find((n) => `/${n[0]}` === pathname)?.[1] || 'Dashboard';
  const [query, setQuery] = useState('');
  const [language, setLanguage] = useState('en');
  const [providerState, setProviderState] = useState<'loading' | 'ready' | 'unavailable'>('loading');

  useEffect(() => {
    let active = true;
    api('/status')
      .then((data: any) => {
        if (!active) return;
        const entries = Object.values(data?.providers || {});
        setProviderState(
          entries.length && entries.some((v) => !['unconfigured', 'unavailable'].includes(String(v)))
            ? 'ready'
            : 'unavailable',
        );
      })
      .catch(() => active && setProviderState('unavailable'));

    return () => {
      active = false;
    };
  }, []);

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

  return (
    <header className="topbar">
      <button type="button" className="icon-button mobile-toggle" onClick={toggle} aria-label="Open navigation">
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
        <kbd>Ctrl K</kbd>
      </form>

      <div className="top-actions">
        <label className="top-language">
          <span className="sr-only">Preferred response language</span>
          <select aria-label="Preferred response language" suppressHydrationWarning value={language} onChange={(event) => changeLanguage(event.target.value)}>
            <option value="en">EN</option><option value="hi">हि</option><option value="mr">म</option>
          </select>
        </label>
        <button type="button" className="notification-button" aria-label="Notifications"><Bell size={17} aria-hidden="true" /></button>
        <button type="button" className="evidence-toggle" onClick={onToggleEvidence} aria-label="Toggle evidence panel" aria-controls="evidence-panel">
          <span className="evidence-toggle__icon" aria-hidden="true">◫</span>
          <span className="evidence-toggle__label">Evidence</span>
        </button>

        <span className={`provider-pulse ${providerState}`}>
          <i />
          {providerState === 'loading'
            ? 'Checking providers'
            : providerState === 'ready'
              ? 'Provider state: Ready'
              : 'Provider state: Unavailable'}
        </span>

        <Link href="/settings" className="profile-link" aria-label="Open settings">
          <span className="avatar">OM</span>
          <span>
            <b>Omkar</b>
            <small>Researcher</small>
          </span>
          <em>⌄</em>
        </Link>
      </div>
    </header>
  );
}
