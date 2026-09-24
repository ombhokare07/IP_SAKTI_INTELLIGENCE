'use client';

import dynamic from 'next/dynamic';
import type { ScreeningPageName } from '@/components/features/ScreeningPage';

function ModuleSkeleton() {
  return <div className="module-skeleton" role="status" aria-label="Loading workspace module">
    <span className="module-skeleton__eyebrow" />
    <span className="module-skeleton__title" />
    <span className="module-skeleton__copy" />
    <div className="module-skeleton__surface"><i /><i /><i /></div>
  </div>;
}

const loading = () => <ModuleSkeleton />;
const DashboardPage = dynamic(() => import('@/components/dashboard/DashboardPage'), { loading });
const ScreeningPage = dynamic(() => import('@/components/features/ScreeningPage'), { loading });
const KnowledgeLibraryPage = dynamic(() => import('@/components/workspace/KnowledgeLibraryPage'), { loading });
const RegulationChangesPage = dynamic(
  () => import('@/components/workspace/MonitoringPages').then((module) => module.RegulationChangesPage),
  { loading },
);
const RegulatoryAlertsPage = dynamic(
  () => import('@/components/workspace/MonitoringPages').then((module) => module.RegulatoryAlertsPage),
  { loading },
);
const ReportsPage = dynamic(() => import('@/components/workspace/ReportsPage'), { loading });
const SettingsPage = dynamic(() => import('@/components/workspace/SettingsPage'), { loading });

const screeningPages = new Set<ScreeningPageName>([
  'ask',
  'patentability',
  'prior-art',
  'tk-risk',
  'regulation-compare',
  'document-checker',
  'compliance-journey',
]);

export default function WorkspacePage({ page }: { page: string }) {
  if (page === 'dashboard') return <DashboardPage />;
  if (screeningPages.has(page as ScreeningPageName)) return <ScreeningPage page={page as ScreeningPageName} />;
  if (page === 'knowledge-library') return <KnowledgeLibraryPage />;
  if (page === 'regulation-changes') return <RegulationChangesPage />;
  if (page === 'regulatory-alerts') return <RegulatoryAlertsPage />;
  if (page === 'reports') return <ReportsPage />;
  return <SettingsPage />;
}
