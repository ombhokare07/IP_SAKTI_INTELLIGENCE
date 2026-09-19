from uuid import uuid4
from intelligence.contracts import now_iso
from reports.renderer import markdown_report,html_report

class ReportService:
    def __init__(self,database):self.db=database
    def create(self,title,kind,assessment):
        mode=assessment.get('mode') or assessment.get('search_summary',{}).get('provider_mode') or ('local' if assessment.get('citations') else 'unconfigured')
        report={'id':uuid4().hex,'title':title,'kind':kind,'created_at':now_iso(),'mode':mode,'assessment':assessment}
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
