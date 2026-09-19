import math
from intelligence.contracts import screening_trust
from intelligence.regulations.jurisdiction_engine import normalize_jurisdiction
from intelligence.compliance.requirement_extractor import extract_requirements
from intelligence.compliance.missing_field_detector import extract_document_fields,detect_missing_fields,is_missing
from intelligence.compliance.compliance_score import calculate_compliance_score

class ComplianceChecker:
    def __init__(self,regulation_engine):self.regulations=regulation_engine
    def check(self,payload):
        jurisdiction=normalize_jurisdiction(payload.get('jurisdiction','IN'))
        category=payload.get('product_category','herbal_product')
        versions=self.regulations.tracker.current(jurisdiction,category,mode=self.regulations.mode,as_of=payload.get('as_of')) if self.regulations.provider else []
        requirements=extract_requirements(versions)
        fields={**extract_document_fields(payload.get('document_text','')),**payload.get('fields',{})}
        checks=[]
        for r in requirements:
            value=fields.get(r['field'])
            status='missing' if is_missing(value) else 'provided_unverified'
            if status!='missing' and r['operator']=='equals' and str(value).strip().casefold()!=str(r['expected']).strip().casefold():status='rule_mismatch'
            if status!='missing' and r['operator']=='minimum':
                try:
                    numeric=float(value)
                    if not math.isfinite(numeric) or numeric<float(r['expected']):status='rule_mismatch'
                except (ValueError,TypeError):status='manual_review'
            checks.append({**r,'status':status,'supplied_value':value})
        citations=[{**v['evidence'],'jurisdiction':v['jurisdiction'],'regulation_id':v['regulation_id'],'version':v['version']} for v in versions]
        return {'status':'screened' if requirements else 'insufficient_evidence','mode':self.regulations.mode,
                'jurisdiction':jurisdiction,'product_category':category,'fields':fields,'checks':checks,
                'missing_fields':detect_missing_fields(requirements,fields),'score':calculate_compliance_score(checks),
                'legal_compliance':'undetermined','citations':citations,'versions':[{'id':v['regulation_id'],'version':v['version'],'effective_from':v['effective_from']} for v in versions],
                'trust':screening_trust(citations,mode=self.regulations.mode),'sync':self.regulations.sync_status,
                'limitations':(['TEST DATA ONLY: requirements are synthetic fixtures.'] if self.regulations.mode=='mock' else [])+[
                    'No evidence -> no definitive conclusion. No loaded rule means the requirement is unknown.',
                    'Provided fields are user assertions; matching a rule does not verify accuracy, authenticity, safety or legal compliance.',
                    'Prose requirements require a curated field mapping with an exact source excerpt.']}
