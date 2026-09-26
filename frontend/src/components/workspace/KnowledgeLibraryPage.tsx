'use client';

import { useEffect, useRef, useState } from 'react';
import { ArrowDownToLine, BookOpen, Database, File, FileSearch, Library, RefreshCw, X } from 'lucide-react';
import DocumentUploader from '@/components/DocumentUploader';
import { Empty, Notice } from '@/components/ResultView';
import { ErrorState, LoadingState, PageHeader, formatFileSize, formatLocalTime } from '@/components/ui/WorkspaceUI';
import { useResource } from '@/hooks/useResource';
import { api, download } from '@/services/api';
import { pulseScene, setSceneMetrics, setScenePhase } from '@/services/scene-signals.mjs';
import type { DocumentsResponse, DocumentSummary, WorkspaceStatus } from '@/types/api';

type DocumentDetail = DocumentSummary & {
  pages?: Array<{ page?: number; text?: string }>;
  sha256?: string;
};

export default function KnowledgeLibraryPage() {
  const documents = useResource<DocumentsResponse>('/documents');
  const status = useResource<WorkspaceStatus>('/status');
  const [selected, setSelected] = useState<DocumentDetail | null>(null);
  const [message, setMessage] = useState('');
  const [indexing, setIndexing] = useState('');
  const closeRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!selected) return;
    const previous = document.activeElement as HTMLElement | null;
    const close = (event: KeyboardEvent) => event.key === 'Escape' && setSelected(null);
    document.addEventListener('keydown', close);
    document.body.style.overflow = 'hidden';
    closeRef.current?.focus();
    return () => {
      document.removeEventListener('keydown', close);
      document.body.style.overflow = '';
      previous?.focus();
    };
  }, [selected]);

  const inspect = async (id: string) => {
    setMessage('');
    try { setSelected(await api(`/documents/${id}`) as DocumentDetail); pulseScene('document-opened'); }
    catch (reason) { setMessage(reason instanceof Error ? reason.message : 'The document could not be opened.'); }
  };

  const indexDocument = async (document: DocumentSummary) => {
    setIndexing(document.id); setMessage(''); setScenePhase('processing');
    try {
      const response: any = await api(`/documents/${document.id}/ingest`, {});
      setMessage(`${String(response.status).replaceAll('_', ' ')}: ${response.stored_chunks} chunks stored.`);
      documents.reload(); status.reload();
      setScenePhase('success', 'document-indexed');
    } catch (reason) {
      setMessage(reason instanceof Error ? reason.message : 'The document could not be indexed.');
      setScenePhase('error', 'document-error');
    } finally { setIndexing(''); }
  };

  const list = documents.data?.documents || [];
  const indexed = list.filter((document) => document.rag_indexed).length;
  const verified = list.filter((document) => document.source_verified).length;
  const chunks = status.data?.rag?.knowledge_base?.indexed_chunks;
  useEffect(() => { setSceneMetrics({ nodeCount: list.length, density: typeof chunks === 'number' ? chunks : undefined }); }, [chunks, list.length]);

  return <div className="workspace-page library-page">
    <PageHeader page="knowledge-library" description="Upload, inspect, download and index source documents without implying that stored material has been verified." action={<button className="button secondary" type="button" onClick={() => { documents.reload(); status.reload(); }}><RefreshCw size={15} />Refresh</button>} />
    {message && <Notice>{message}</Notice>}
    <section className="library-metrics" aria-label="Knowledge library overview">
      <article className="depth-card"><span><Library size={18} /></span><div><strong>{documents.busy ? '—' : list.length}</strong><small>Stored documents</small></div></article>
      <article className="depth-card"><span><Database size={18} /></span><div><strong>{status.busy ? '—' : typeof chunks === 'number' ? chunks : 'Unavailable'}</strong><small>Indexed chunks</small></div></article>
      <article className="depth-card"><span><BookOpen size={18} /></span><div><strong>{documents.busy ? '—' : indexed}</strong><small>RAG-indexed files</small></div></article>
      <article className="depth-card"><span><FileSearch size={18} /></span><div><strong>{documents.busy ? '—' : verified}</strong><small>Source-verified records</small></div></article>
    </section>
    <div className="library-layout">
      <section className="panel library-panel"><div className="section-title"><div><span className="eyebrow">SOURCE LIBRARY</span><h2>Workspace documents</h2></div><small>{list.length ? `${list.length} backend record${list.length === 1 ? '' : 's'}` : 'No inferred counts'}</small></div>
        {documents.busy ? <LoadingState label="Loading source records…" /> : documents.error ? <ErrorState error={documents.error} retry={documents.reload} /> : list.length ? <div className="document-list">{list.map((document) => <article className="document-card depth-card" key={document.id}><span className="file-icon"><File size={17} /></span><div className="document-card__body"><div className="document-card__title"><strong>{document.name}</strong><span className={`badge${document.status === 'no_extractable_text' ? ' warning' : ''}`}>{document.status === 'no_extractable_text' ? 'No extractable text' : 'Stored'}</span></div><div className="document-facts"><span>{document.page_count ? `${document.page_count} pages` : 'Text document'}</span><span>{formatFileSize(document.size_bytes)}</span><span>{document.source_verified ? 'Source verified' : 'Source unverified'}</span><span className={document.rag_indexed ? 'positive' : 'muted'}>{document.rag_indexed ? 'Indexed for RAG' : 'Not indexed'}</span></div><div className="inline-actions"><button className="button secondary small" type="button" onClick={() => inspect(document.id)}>Inspect</button>{document.extension === '.pdf' && <button className="button ghost small" type="button" disabled={Boolean(indexing)} onClick={() => indexDocument(document)}><Database size={14} />{indexing === document.id ? 'Indexing…' : document.rag_indexed ? 'Reindex' : 'Index for RAG'}</button>}<button className="button ghost small" type="button" onClick={() => download(`/documents/${document.id}/file`, document.name).catch((reason) => setMessage(reason.message))}><ArrowDownToLine size={14} />Download</button></div></div></article>)}</div> : <Empty title="Your library is empty">Add a source document to inspect its extracted text or use it in a compliance workflow.</Empty>}
      </section>
      <aside><DocumentUploader onUploaded={(document) => { setSelected(document); documents.reload(); status.reload(); setScenePhase('success', 'document-uploaded'); }} /><div className="library-guidance"><strong>Source discipline</strong><p>Uploads are stored records, not automatically authoritative sources. Check provenance and effective dates before relying on them.</p></div></aside>
    </div>
    {selected && <><button type="button" className="detail-scrim" aria-label="Close document inspector" onClick={() => setSelected(null)} /><aside className="document-drawer" role="dialog" aria-modal="true" aria-labelledby="document-detail-title"><div className="document-drawer__header"><div><span className="eyebrow">DOCUMENT INSPECTOR</span><h2 id="document-detail-title">{selected.name}</h2></div><button ref={closeRef} className="panel-close" type="button" aria-label="Close document inspector" onClick={() => setSelected(null)}><X size={18} /></button></div><div className="document-drawer__body"><div className="document-facts prominent"><span>{selected.extension?.slice(1).toUpperCase()}</span><span>{selected.page_count ? `${selected.page_count} pages` : 'Text document'}</span><span>{formatFileSize(selected.size_bytes)}</span><span>{selected.rag_indexed ? 'Indexed for RAG' : 'Not indexed'}</span></div><Notice>Stored content is not automatically verified or authoritative. Scanned PDFs may require OCR outside this application.</Notice><div className="document-pages">{selected.pages?.length ? selected.pages.map((page, index) => <article className="document-page" key={page.page || index}><span className="eyebrow">{page.page ? `PAGE ${page.page}` : 'DOCUMENT TEXT'}</span><pre>{page.text || 'No extractable text on this page.'}</pre></article>) : <Empty title="No extractable text">The stored record does not expose page text. Download the original for manual review.</Empty>}</div><details className="raw-detail compact"><summary>Technical details</summary><dl className="technical-list"><div><dt>Document ID</dt><dd><code>{selected.id}</code></dd></div>{selected.sha256 && <div><dt>SHA-256</dt><dd><code>{selected.sha256}</code></dd></div>}<div><dt>Stored</dt><dd>{formatLocalTime(selected.created_at)}</dd></div></dl></details></div></aside></>}
  </div>;
}
