'use client';

import { Component, type ErrorInfo, type ReactNode, useEffect, useMemo, useState } from 'react';
import dynamic from 'next/dynamic';
import { usePathname } from 'next/navigation';

const PersistentWorkspaceScene = dynamic(() => import('./PersistentWorkspaceScene'), {
  ssr: false,
  loading: () => null,
});

class WorkspaceSceneBoundary extends Component<{ children: ReactNode; fallback: ReactNode }, { failed: boolean }> {
  state = { failed: false };
  static getDerivedStateFromError() { return { failed: true }; }
  componentDidCatch(_error: Error, _info: ErrorInfo) { /* Decorative WebGL safely falls back. */ }
  render() { return this.state.failed ? this.props.fallback : this.props.children; }
}

function supportsWebGL() {
  try {
    const canvas = document.createElement('canvas');
    return Boolean(window.WebGLRenderingContext && (canvas.getContext('webgl') || canvas.getContext('experimental-webgl')));
  } catch {
    return false;
  }
}

export type WorkspaceSceneKey =
  | 'dashboard' | 'ask' | 'patentability' | 'prior-art' | 'tk-risk'
  | 'regulation-compare' | 'document-checker' | 'regulation-changes'
  | 'compliance-journey' | 'regulatory-alerts' | 'knowledge-library'
  | 'reports' | 'settings';

export function sceneKeyForPath(pathname: string): WorkspaceSceneKey {
  const key = pathname.split('/').filter(Boolean)[0] as WorkspaceSceneKey | undefined;
  const known: WorkspaceSceneKey[] = [
    'dashboard', 'ask', 'patentability', 'prior-art', 'tk-risk', 'regulation-compare',
    'document-checker', 'regulation-changes', 'compliance-journey', 'regulatory-alerts',
    'knowledge-library', 'reports', 'settings',
  ];
  return key && known.includes(key) ? key : 'dashboard';
}

function StaticWorkspaceField({ scene }: { scene: WorkspaceSceneKey }) {
  return <div className="workspace-field-fallback" data-static-scene={scene}>
    <i className="field-core" /><i className="field-orbit field-orbit--a" /><i className="field-orbit field-orbit--b" />
    <i className="field-trace field-trace--a" /><i className="field-trace field-trace--b" />
  </div>;
}

export default function PersistentWorkspaceVisual() {
  const pathname = usePathname();
  const scene = useMemo(() => sceneKeyForPath(pathname), [pathname]);
  const [renderMode, setRenderMode] = useState<'fallback' | 'compact' | 'full'>('fallback');

  useEffect(() => {
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
    const mobile = window.matchMedia('(max-width: 640px)');
    const tablet = window.matchMedia('(max-width: 1100px)');
    const update = () => setRenderMode(
      reduced.matches || mobile.matches || !supportsWebGL() ? 'fallback' : tablet.matches ? 'compact' : 'full',
    );
    update();
    reduced.addEventListener('change', update);
    mobile.addEventListener('change', update);
    tablet.addEventListener('change', update);
    return () => {
      reduced.removeEventListener('change', update);
      mobile.removeEventListener('change', update);
      tablet.removeEventListener('change', update);
    };
  }, []);

  const fallback = <StaticWorkspaceField scene={scene} />;
  return <div className="global-workspace-field" data-global-canvas data-scene={scene} aria-hidden="true">
    {renderMode === 'fallback' ? fallback : (
      <WorkspaceSceneBoundary fallback={fallback}>
        <PersistentWorkspaceScene scene={scene} compact={renderMode === 'compact'} />
      </WorkspaceSceneBoundary>
    )}
  </div>;
}
