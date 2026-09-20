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

  return (
    <article className={`source-card${expanded ? ' is-expanded' : ''}`}>
      <div className="source-heading">
        <span className="source-index" aria-hidden="true">{citation.citation_id || index + 1}</span>
        <div>
          <strong>{citation.title || citation.source || 'Retrieved source'}</strong>
          <small>{sourceMeta}{citation.page ? ` · Page ${citation.page}` : ''}</small>
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
        ? <a href={url} target="_blank" rel="noreferrer">Open supplied source <span aria-hidden="true">↗</span></a>
        : <span className="source-locator">{citation.locator || citation.publication_number || citation.source || 'Source URL unavailable'}</span>}
    </article>
  );
}
