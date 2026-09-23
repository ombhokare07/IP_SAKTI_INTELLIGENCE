'use client';

import { useCallback, useEffect, useState } from 'react';
import { api } from '@/services/api';

export interface ResourceState<T> {
  data: T | null;
  error: string;
  busy: boolean;
  reload: () => void;
}

export function useResource<T>(path: string, enabled = true): ResourceState<T> {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(true);
  const [nonce, setNonce] = useState(0);

  useEffect(() => {
    if (!enabled) {
      setBusy(false);
      setError('');
      return;
    }
    let active = true;
    setBusy(true);
    setError('');
    api(path)
      .then((value) => {
        if (active) setData(value as T);
      })
      .catch((reason: unknown) => {
        if (active) setError(reason instanceof Error ? reason.message : 'The request could not be completed.');
      })
      .finally(() => {
        if (active) setBusy(false);
      });
    return () => {
      active = false;
    };
  }, [enabled, path, nonce]);

  const reload = useCallback(() => setNonce((value) => value + 1), []);
  return { data, error, busy, reload };
}
