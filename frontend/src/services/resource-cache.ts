import { api } from './api';

type CacheEntry = {
  data?: unknown;
  error?: string;
  updatedAt: number;
  promise?: Promise<unknown>;
};

export type ResourceSnapshot<T> = {
  data: T | null;
  error: string;
  loading: boolean;
  stale: boolean;
};

const entries = new Map<string, CacheEntry>();
const listeners = new Map<string, Set<() => void>>();

export function resourceTtl(path: string) {
  if (path === '/auth/me') return 5 * 60_000;
  if (path === '/status') return 45_000;
  if (path === '/documents' || path === '/reports') return 20_000;
  return 30_000;
}

function emit(path: string) {
  listeners.get(path)?.forEach((listener) => listener());
}

export function subscribeResource(path: string, listener: () => void) {
  const pathListeners = listeners.get(path) || new Set<() => void>();
  pathListeners.add(listener);
  listeners.set(path, pathListeners);
  return () => {
    pathListeners.delete(listener);
    if (!pathListeners.size) listeners.delete(path);
  };
}

export function getResourceSnapshot<T>(path: string, ttlMs = resourceTtl(path)): ResourceSnapshot<T> {
  const entry = entries.get(path);
  return {
    data: (entry?.data as T | undefined) ?? null,
    error: entry?.error || '',
    loading: Boolean(entry?.promise),
    stale: !entry?.updatedAt || Date.now() - entry.updatedAt >= ttlMs,
  };
}

export function loadResource<T>(path: string, options: { force?: boolean; ttlMs?: number } = {}) {
  const ttlMs = options.ttlMs ?? resourceTtl(path);
  const current = entries.get(path);
  if (current?.promise) return current.promise as Promise<T>;
  if (!options.force && current?.data !== undefined && Date.now() - current.updatedAt < ttlMs) {
    return Promise.resolve(current.data as T);
  }

  const entry: CacheEntry = current || { updatedAt: 0 };
  entry.error = '';
  entry.promise = api(path)
    .then((data) => {
      entry.data = data;
      entry.updatedAt = Date.now();
      entry.error = '';
      return data;
    })
    .catch((reason: unknown) => {
      entry.error = reason instanceof Error ? reason.message : 'The request could not be completed.';
      throw reason;
    })
    .finally(() => {
      entry.promise = undefined;
      emit(path);
    });
  entries.set(path, entry);
  emit(path);
  return entry.promise as Promise<T>;
}

export function invalidateResource(path: string) {
  const entry = entries.get(path);
  if (entry) entry.updatedAt = 0;
  emit(path);
}

export function clearResourceCache() {
  const paths = [...entries.keys()];
  entries.clear();
  paths.forEach(emit);
}
