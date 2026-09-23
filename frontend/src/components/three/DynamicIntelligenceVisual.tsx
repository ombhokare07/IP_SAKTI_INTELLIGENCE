'use client';

import { Component, type ErrorInfo, type ReactNode, useEffect, useState } from 'react';
import dynamic from 'next/dynamic';

const IntelligenceScene = dynamic(() => import('./IntelligenceScene'), {
  ssr: false,
  loading: () => <StaticIntelligenceVisual />,
});

class SceneBoundary extends Component<{ children: ReactNode; fallback: ReactNode }, { failed: boolean }> {
  state = { failed: false };
  static getDerivedStateFromError() { return { failed: true }; }
  componentDidCatch(_error: Error, _info: ErrorInfo) { /* Decorative scene safely falls back. */ }
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

export function StaticIntelligenceVisual({ compact = false }: { compact?: boolean }) {
  return <figure className={`intelligence-fallback${compact ? ' compact' : ''}`} aria-hidden="true">
    <span className="fallback-orbit orbit-a" /><span className="fallback-orbit orbit-b" />
    <span className="fallback-core"><i /><i /><i /></span>
    {[0, 1, 2, 3, 4, 5].map((index) => <span className={`fallback-node node-${index + 1}`} key={index} />)}
    <span className="fallback-leaf leaf-a" /><span className="fallback-leaf leaf-b" /><span className="fallback-leaf leaf-c" />
  </figure>;
}

export default function DynamicIntelligenceVisual({ className = '', compact = false }: { className?: string; compact?: boolean }) {
  const [enabled, setEnabled] = useState(false);

  useEffect(() => {
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
    const narrow = window.matchMedia('(max-width: 960px)');
    const update = () => setEnabled(!reduced.matches && !narrow.matches && supportsWebGL());
    update();
    reduced.addEventListener('change', update);
    narrow.addEventListener('change', update);
    return () => {
      reduced.removeEventListener('change', update);
      narrow.removeEventListener('change', update);
    };
  }, []);

  const fallback = <StaticIntelligenceVisual compact={compact} />;
  return <div className={`intelligence-visual ${className}`} aria-hidden="true">
    {enabled ? <SceneBoundary fallback={fallback}><IntelligenceScene /></SceneBoundary> : fallback}
  </div>;
}

