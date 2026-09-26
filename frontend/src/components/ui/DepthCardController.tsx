'use client';

import { useEffect } from 'react';

export default function DepthCardController() {
  useEffect(() => {
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
    const desktop = window.matchMedia('(min-width: 768px)');
    let active: HTMLElement | null = null;
    let frame = 0;
    let clientX = 0;
    let clientY = 0;

    const reset = (element: HTMLElement | null) => {
      if (!element) return;
      element.style.setProperty('--depth-rx', '0deg');
      element.style.setProperty('--depth-ry', '0deg');
      element.style.setProperty('--depth-glow-x', '50%');
      element.style.setProperty('--depth-glow-y', '50%');
    };
    const paint = () => {
      frame = 0;
      if (!active || reduced.matches || !desktop.matches) return;
      const bounds = active.getBoundingClientRect();
      const x = Math.max(0, Math.min(1, (clientX - bounds.left) / Math.max(1, bounds.width)));
      const y = Math.max(0, Math.min(1, (clientY - bounds.top) / Math.max(1, bounds.height)));
      active.style.setProperty('--depth-rx', `${((.5 - y) * 3.2).toFixed(2)}deg`);
      active.style.setProperty('--depth-ry', `${((x - .5) * 4.2).toFixed(2)}deg`);
      active.style.setProperty('--depth-glow-x', `${(x * 100).toFixed(1)}%`);
      active.style.setProperty('--depth-glow-y', `${(y * 100).toFixed(1)}%`);
    };
    const move = (event: PointerEvent) => {
      const target = (event.target as HTMLElement | null)?.closest<HTMLElement>('.depth-card') ?? null;
      if (target !== active) { reset(active); active = target; }
      if (!active) return;
      clientX = event.clientX; clientY = event.clientY;
      if (!frame) frame = window.requestAnimationFrame(paint);
    };
    const leave = (event: PointerEvent) => {
      if (!active) return;
      const related = event.relatedTarget as Node | null;
      if (related && active.contains(related)) return;
      reset(active); active = null;
    };
    const disable = () => { reset(active); active = null; };

    document.addEventListener('pointermove', move, { passive: true });
    document.addEventListener('pointerout', leave, { passive: true });
    reduced.addEventListener('change', disable); desktop.addEventListener('change', disable);
    return () => {
      document.removeEventListener('pointermove', move); document.removeEventListener('pointerout', leave);
      reduced.removeEventListener('change', disable); desktop.removeEventListener('change', disable);
      if (frame) window.cancelAnimationFrame(frame); reset(active);
    };
  }, []);
  return null;
}
