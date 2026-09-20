"""Deterministic report exports preserve provenance and uncertainty; no generated claims."""
import html
import json

NOTICE='SCREENING REPORT — not a legal opinion. Scores measure screening/evidence/grounding quality, not legal correctness or probability of patent grant.'

def markdown_report(report):
    # JSON inside a fence preserves every source and limitation without prose fabrication.
    data=json.dumps(report['assessment'],ensure_ascii=False,indent=2)
    fence='`'*max(3,max((len(part) for part in __import__('re').findall(r'`+',data)),default=0)+1)
    task=report.get('task') or report.get('kind','screening').replace('_',' ').title()
    source_mode=report.get('source_mode') or report.get('mode','unconfigured')
    return f"# {report['title']}\n\n{NOTICE}\n\nReport ID: {report['id']}\n\nCreated: {report['created_at']}\n\nTask: {task}\n\nEvidence/Source Mode: {source_mode}\n\n{fence}json\n{data}\n{fence}\n"

def html_report(report):
    title=html.escape(report['title'])
    data=html.escape(json.dumps(report['assessment'],ensure_ascii=False,indent=2))
    task=html.escape(report.get('task') or report.get('kind','screening').replace('_',' ').title())
    source_mode=html.escape(report.get('source_mode') or report.get('mode','unconfigured'))
    return f'<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>{title}</title><style>body{{font:16px/1.6 system-ui;max-width:1050px;margin:40px auto;padding:24px;color:#152845}}pre{{white-space:pre-wrap;overflow-wrap:anywhere;background:#f2f5fa;padding:24px;font:14px/1.6 monospace}}.notice{{border-left:4px solid #db940a;padding:16px;background:#fff7db}}@media print{{body{{margin:0}}pre{{font-size:11px}}}}</style><h1>{title}</h1><p class="notice">{NOTICE}</p><p>Created: {html.escape(report["created_at"])} · Task: {task} · Evidence/Source Mode: {source_mode}</p><pre>{data}</pre></html>'
