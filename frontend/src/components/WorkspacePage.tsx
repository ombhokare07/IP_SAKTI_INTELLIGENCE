'use client';

import DashboardPage from '@/components/dashboard/DashboardPage';
import ScreeningPage, { type ScreeningPageName } from '@/components/features/ScreeningPage';
import KnowledgeLibraryPage from '@/components/workspace/KnowledgeLibraryPage';
import { RegulationChangesPage, RegulatoryAlertsPage } from '@/components/workspace/MonitoringPages';
import ReportsPage from '@/components/workspace/ReportsPage';
import SettingsPage from '@/components/workspace/SettingsPage';

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
