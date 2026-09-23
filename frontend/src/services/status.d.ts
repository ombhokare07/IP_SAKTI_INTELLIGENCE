import type { ProviderStatusValue, WorkspaceStatus } from '@/types/api';

export type StatusTone = 'positive' | 'attention' | 'negative';
export interface StatusPresentation {
  code: string;
  label: string;
  tone: StatusTone;
  connected: boolean;
}

export function statusCode(value: ProviderStatusValue): string;
export function describeStatus(value: ProviderStatusValue): StatusPresentation;
export function isVerifiedConnection(value: ProviderStatusValue): boolean;
export function authSessionStatus(status?: WorkspaceStatus | null): StatusPresentation;
export function countConnectedProviders(providers?: Record<string, ProviderStatusValue>): number;
export function summarizeProviders(providers?: Record<string, ProviderStatusValue>): {
  connected: number;
  total: number;
  label: string;
  tone: StatusTone;
};
