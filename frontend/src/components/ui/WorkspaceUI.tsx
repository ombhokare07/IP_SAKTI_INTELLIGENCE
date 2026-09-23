'use client';

import type { ReactNode } from 'react';
import Link from 'next/link';
import { AlertTriangle, LoaderCircle, RotateCcw } from 'lucide-react';
import { describeStatus } from '@/services/status.mjs';
import type { ProviderStatusValue } from '@/types/api';
import { Notice } from '@/components/ResultView';
import { navigation } from '@/components/Sidebar';

export function LoadingState({ label = 'Loading workspace data…' }: { label?: string }) {
  return <div className="loading-state" role="status"><LoaderCircle aria-hidden="true" />{label}</div>;
}

export function ErrorState({ error, retry }: { error: string; retry?: () => void }) {
  return <Notice type="error"><AlertTriangle size={18} aria-hidden="true" /><div><strong>Request could not be completed.</strong><p>{error}</p><div className="inline-actions">{retry && <button className="button secondary small" type="button" onClick={retry}><RotateCcw size={14} />Retry</button>}<Link className="text-link" href="/settings">Check settings</Link></div></div></Notice>;
}

export function PageHeader({ page, description, action, eyebrow = 'IP-SAKTI / INTELLIGENCE' }: { page: string; description: string; action?: ReactNode; eyebrow?: string }) {
  return <header className="page-header"><div><span className="eyebrow">{eyebrow}</span><h1>{navigation.find((item) => item[0] === page)?.[1] || page}</h1><p>{description}</p></div>{action && <div className="page-header__action">{action}</div>}</header>;
}

export function StatusBadge({ value, label }: { value: ProviderStatusValue; label?: string }) {
  const state = describeStatus(value);
  return <span className={`status-badge ${state.tone}`} title={state.code}><i aria-hidden="true" />{label || state.label}</span>;
}

export function formatFileSize(bytes: number) {
  if (!Number.isFinite(bytes)) return 'Size unavailable';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function formatLocalTime(value?: string) {
  if (!value) return 'Date unavailable';
  const canonical = /(?:Z|[+-]\d\d:\d\d)$/i.test(value) ? value : `${value}Z`;
  const date = new Date(canonical);
  if (Number.isNaN(date.getTime())) return 'Date unavailable';
  try {
    return new Intl.DateTimeFormat(undefined, { year: 'numeric', month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit', timeZoneName: 'short' }).format(date);
  } catch {
    return date.toLocaleString();
  }
}

