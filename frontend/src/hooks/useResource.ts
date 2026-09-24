'use client';

import { useCallback, useEffect, useState } from 'react';
import {
  getResourceSnapshot,
  loadResource,
  resourceTtl,
  subscribeResource,
  type ResourceSnapshot,
} from '@/services/resource-cache';

export interface ResourceState<T> {
  data: T | null;
  error: string;
  busy: boolean;
  reload: () => void;
}

export function useResource<T>(path: string, enabled = true): ResourceState<T> {
  const ttlMs = resourceTtl(path);
  const [snapshot, setSnapshot] = useState<ResourceSnapshot<T>>(() => getResourceSnapshot<T>(path, ttlMs));
  const [nonce, setNonce] = useState(0);

  useEffect(() => {
    if (!enabled) {
      setSnapshot({ data: null, error: '', loading: false, stale: false });
      return;
    }
    const update = () => setSnapshot(getResourceSnapshot<T>(path, ttlMs));
    const unsubscribe = subscribeResource(path, update);
    update();
    loadResource<T>(path, { force: nonce > 0, ttlMs }).catch(() => undefined);
    return unsubscribe;
  }, [enabled, nonce, path, ttlMs]);

  const reload = useCallback(() => setNonce((value) => value + 1), []);
  return {
    data: snapshot.data,
    error: snapshot.error,
    busy: enabled && snapshot.data === null && snapshot.loading,
    reload,
  };
}
