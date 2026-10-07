'use client';

import {useState} from 'react';
import {describeMode, safeSourceUrl} from '@/services/protocol.mjs';

type Citation = {
  citation_id?: string | number;
  title?: string;
  source?: string;
  authority?: string;
  provider?: string;
  mode?: string;
  page?: string | number;
  excerpt?: string;
  text?: string;
  source_url?: string;
  locator?: string;
  publication_number?: string;
};

export default function CitationCard({citation, index = 0}: {citation: Citation; index?: number}) {
  const [expanded, setExpanded] = useState(false);
  const url = safeSourceUrl(citation.source_url);
  const excerpt = citation.excerpt || citation.text || 'No excerpt was supplied. Inspect the source record before relying on it.';
  const isExpandable = excerpt.length > 220;
  const sourceMeta = citation.authority || citation.provider || describeMode(citation.mode || 'local');
  const title = citation.title || citation.source || 'Retrieved source';
  const marker = citation.citation_id ?? index + 1;
  const locator = citation.locator || citation.publication_number || citation.source;
  const repeatedLocator = typeof locator === 'string' && locator.trim().toLocaleLowerCase() === title.trim().toLocaleLowerCase();

  return (
    <article className={`source-card${expanded ? ' is-expanded' : ''}`}>
      <div className="source-heading">
        <span className="source-index" aria-label={`Citation ${marker}`}>[{marker}]</span>
        <div>
          <strong className="source-title" title={title}>{title}</strong>
          <small className="source-meta">{sourceMeta}</small>
          {citation.page !== null && citation.page !== undefined && citation.page !== '' && <small className="source-page">Page {citation.page}</small>}
        </div>
      </div>
      <blockquote className="source-excerpt">{excerpt}</blockquote>
      {isExpandable && (
        <button
          className="text-button source-toggle"
          type="button"
          onClick={() => setExpanded((current) => !current)}
          aria-expanded={expanded}
        >
          {expanded ? 'Show less' : 'Read more'}
        </button>
      )}
      {url
        ? <a href={url} target="_blank" rel="noreferrer">Open source <span aria-hidden="true">↗</span></a>
        : <span className="source-locator">{locator && !repeatedLocator ? locator : 'Source URL unavailable'}</span>}
    </article>
  );
}
