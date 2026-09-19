class ComplianceJourneyGenerator:
    def __init__(self,checker):self.checker=checker
    def generate(self,payload):
        result=self.checker.check(payload)
        steps=[{'id':'verify_sources','title':'Verify applicable sources and product classification','status':'review_required','depends_on':[],'evidence_ids':[e['id'] for e in result['citations']]}]
        if not result['checks']:
            steps.append({'id':'obtain_requirements','title':'Obtain current authoritative requirements for this product and jurisdiction','status':'action_required','depends_on':['verify_sources'],'evidence_ids':[]})
        for index,check in enumerate(result['checks']):
            steps.append({'id':f'requirement_{index}','title':f'{"Provide" if check["status"]=="missing" else "Review"} {check["label"]}',
                          'status':'action_required' if check['status'] in {'missing','rule_mismatch'} else 'review_required',
                          'depends_on':['verify_sources'],'evidence_ids':[check['evidence_id']],'field':check['field']})
        steps.append({'id':'professional_review','title':'Request qualified professional review before submission','status':'review_required','depends_on':[s['id'] for s in steps[1:]] or ['verify_sources'],'evidence_ids':[]})
        return {'status':result['status'],'mode':result['mode'],'jurisdiction':result['jurisdiction'],'steps':steps,'assessment':result,'citations':result['citations'],'limitations':['This journey is a screening checklist. No submission, approval, fee, deadline or regulatory clearance is implied.']}
