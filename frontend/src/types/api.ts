export type ProviderStatusCode =
  | 'ready'
  | 'live'
  | 'local'
  | 'connected'
  | 'available'
  | 'initialized'
  | 'indexed'
  | 'enabled'
  | 'configured'
  | 'configured_not_verified'
  | 'partial'
  | 'degraded'
  | 'authorization_required'
  | 'mock'
  | 'synthetic'
  | 'unavailable'
  | 'unconfigured'
  | 'not_configured'
  | 'not_connected'
  | 'not connected'
  | 'empty'
  | 'not_indexed'
  | 'disabled'
  | string;

export type ProviderStatusValue =
  | ProviderStatusCode
  | null
  | undefined
  | {
      status?: ProviderStatusCode;
      provider?: string | null;
      execution?: 'local' | 'remote' | 'online' | string | null;
      authorized?: boolean;
      tkdl_connected?: boolean;
      requires_internet?: boolean;
      [key: string]: unknown;
    };

export interface RagStatus {
  status?: ProviderStatusCode;
  gemini_readiness?: ProviderStatusValue;
  embeddings?: ProviderStatusValue & { model?: string | null };
  vector_store_readiness?: ProviderStatusValue;
  knowledge_base?: ProviderStatusValue & { indexed_chunks?: number };
  grounded_chat?: ProviderStatusValue;
  [key: string]: unknown;
}

export interface WorkspaceStatus {
  status?: string;
  version?: string;
  providers?: Record<string, ProviderStatusValue>;
  provider_status?: Record<string, ProviderStatusValue>;
  rag?: RagStatus;
  authentication_required?: boolean;
  authentication?: ProviderStatusValue & {
    google_sign_in?: ProviderStatusCode;
    session_cookie?: ProviderStatusCode;
    legacy_bearer?: ProviderStatusCode;
    legacy_bearer_required?: boolean;
    token_required?: boolean;
  };
  documents?: number;
  reports?: number;
  limitations?: string[];
  configuration_errors?: string[];
  [key: string]: unknown;
}

export interface SessionAccount {
  exists?: boolean;
  id?: number | string;
  created_at?: string;
  updated_at?: string;
  last_login_at?: string;
}

export interface PriorArtSearchSummary {
  search_status: 'complete' | 'partial';
  queries_total: number;
  queries_succeeded: number;
  queries_failed: number;
  provider: string;
  provider_mode: 'mock' | 'live';
  configuration_status: 'mock_test_data' | 'live_configured';
  records_found: number;
  records_analyzed: number;
  cache_hits: number;
  retrieval_timestamp: string;
}

export interface PriorArtSearchResult {
  assessment_id?: string | null;
  search_summary: PriorArtSearchSummary;
  risk?: Record<string, unknown>;
  results: Array<Record<string, unknown>>;
  top_results?: Array<Record<string, unknown>>;
  limitations?: string[];
}

export interface SessionUser {
  email: string;
  name: string;
  picture: string;
  account?: SessionAccount;
}

export interface AuthMeResponse {
  authenticated: boolean;
  user: SessionUser | null;
}

export interface ReportSummary {
  id: string;
  title: string;
  kind?: string;
  task?: string;
  status?: string;
  mode?: string;
  source_mode?: string;
  created_at?: string;
  assessment?: Record<string, unknown>;
  [key: string]: unknown;
}

export interface ReportsResponse {
  reports: ReportSummary[];
}

export interface DocumentSummary {
  id: string;
  name: string;
  extension: string;
  size_bytes: number;
  page_count?: number;
  source_verified?: boolean;
  rag_indexed?: boolean;
  status?: string;
  created_at?: string;
  [key: string]: unknown;
}

export interface DocumentsResponse {
  documents: DocumentSummary[];
}
