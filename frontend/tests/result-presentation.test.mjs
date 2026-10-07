import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import test from 'node:test';

import {
  buildStructuredInspection,
  buildTechnicalRows,
  citationDisplayEntries,
  sanitizeDeveloperPayload,
  shouldShowDeveloperJson,
  statusTone,
} from '../src/services/result-presentation.mjs';

test('technical statuses stay in separate labeled rows with semantic tones', () => {
  const rows = buildTechnicalRows({trace: [
    {agent: 'ayush', status: 'completed'},
    {agent: 'prior_art', status: 'partial'},
    {agent: 'citation', status: 'agent_failed'},
    {agent: 'evidence', status: 'unavailable'},
  ]});
  assert.deepEqual(rows.map(({label, value, tone}) => ({label, value, tone})), [
    {label: 'AYUSH', value: 'Completed', tone: 'completed'},
    {label: 'Prior art', value: 'Partial', tone: 'partial'},
    {label: 'Citation', value: 'Agent failed', tone: 'failed'},
    {label: 'Evidence', value: 'Unavailable', tone: 'unavailable'},
  ]);
  assert.equal(rows.some((row) => row.label.includes(row.value)), false);
  assert.equal(statusTone('configured_not_verified'), 'unavailable');
});

test('structured inspection includes readable limitations but excludes internal retrieval identifiers', () => {
  const result = {
    status: 'grounded', mode: 'local', question: 'Can this be patented?', answer: 'Review evidence [1].',
    citations: [{citation_id: 1, source: '2025.pdf', page: 4, chunk_id: 'chunk-1', vector_id: 'vector-7', embedding_id: 'embed-3', database_id: 'db-2', retrieval_hash: 'hash'}],
    limitations: ['This is a screening result.'],
    trace: [{agent: 'evidence', status: 'completed'}],
  };
  const inspection = buildStructuredInspection(result);
  const serialized = JSON.stringify(inspection);
  assert.match(serialized, /Limitations \(1\)/);
  assert.match(serialized, /This is a screening result\./);
  for (const forbidden of ['chunk-1', 'vector-7', 'embed-3', 'db-2', 'retrieval_hash']) assert.doesNotMatch(serialized, new RegExp(forbidden));
});

test('citation presentation preserves backend order, identifiers and full filename model', async () => {
  const contiguous = citationDisplayEntries([
    {citation_id: 1, source: '2025.pdf'},
    {citation_id: 2, source: 'Long research filename 2026.pdf'},
  ]);
  assert.deepEqual(contiguous.map((entry) => entry.marker), ['[1]', '[2]']);
  assert.equal(contiguous[0].citation.source, '2025.pdf');
  assert.equal(contiguous[1].source, 'Long research filename 2026.pdf');
  assert.equal(contiguous.find((entry) => entry.marker === '[2]').citation.source, 'Long research filename 2026.pdf');

  const irregular = citationDisplayEntries([
    {citation_id: 2, source: 'first.pdf'},
    {citation_id: 2, source: 'duplicate.pdf'},
    {citation_id: 5, source: 'gapped.pdf'},
  ]);
  assert.deepEqual(irregular.map((entry) => entry.marker), ['[2]', '[2]', '[5]']);
  assert.equal(new Set(irregular.map((entry) => entry.key)).size, 3);

  const css = await readFile(new URL('../src/app/globals.css', import.meta.url), 'utf8');
  assert.match(css, /\.source-title[^}]*text-overflow:\s*ellipsis/);
  assert.match(css, /\.source-title[^}]*white-space:\s*nowrap/);
  assert.match(css, /\.source-title[^}]*overflow-wrap:\s*normal/);
});

test('developer JSON requires explicit opt-in and redacts secret-like fields', () => {
  assert.equal(shouldShowDeveloperJson(undefined), false);
  assert.equal(shouldShowDeveloperJson('false'), false);
  assert.equal(shouldShowDeveloperJson('true'), true);
  const sanitized = sanitizeDeveloperPayload({api_key: 'key', nested: {access_token: 'token', password: 'password', safe: 'visible'}});
  assert.deepEqual(sanitized, {api_key: '[REDACTED]', nested: {access_token: '[REDACTED]', password: '[REDACTED]', safe: 'visible'}});
});
