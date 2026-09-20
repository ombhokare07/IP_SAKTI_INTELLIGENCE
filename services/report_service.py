from uuid import uuid4
from intelligence.contracts import now_iso
from reports.renderer import markdown_report,html_report

class ReportService:
    def __init__(self,database):self.db=database
    def create(self,title,kind,assessment):
        mode=assessment.get('mode') or assessment.get('search_summary',{}).get('provider_mode') or ('local' if assessment.get('citations') else 'unconfigured')
        task={
            'ask':'Ask IP-SAKTI','patent':'Patentability','prior_art':'Prior Art',
            'traditional_knowledge':'TK Risk','comparison':'Regulation Compare',
            'compliance':'Document Compliance','journey':'Compliance Journey',
            'changes':'Regulation Changes',
        }.get(kind,kind.replace('_',' ').title())
        search_summary=assessment.get('search_summary') or {}
        if assessment.get('status')=='grounded':
            evidence_mode='grounded'
        elif mode=='mock':
            evidence_mode='synthetic'
        elif mode=='live' and search_summary.get('provider'):
            evidence_mode=str(search_summary['provider'])
        else:
            evidence_mode=mode
        report={'id':uuid4().hex,'title':title,'kind':kind,'task':task,
                'created_at':now_iso(),'mode':mode,'source_mode':evidence_mode,
                'assessment':assessment}
        self.db.put('report',report['id'],report,immutable=True)
        return report
    def list(self):return [{k:v for k,v in r.items() if k!='assessment'} for r in self.db.list('report')]
    def get(self,identifier):return self.db.get('report',identifier)
    def export(self,identifier,format='json'):
        import json
        report=self.get(identifier)
        if not report:raise KeyError(identifier)
        if format=='json':return json.dumps(report,ensure_ascii=False,indent=2),'application/json'
        if format=='markdown':return markdown_report(report),'text/markdown; charset=utf-8'
        if format=='html':return html_report(report),'text/html; charset=utf-8'
        raise ValueError('Use json, markdown or html.')
