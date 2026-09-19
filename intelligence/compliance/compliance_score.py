from intelligence.contracts import SCREENING_NOTICE

def calculate_compliance_score(checks):
    required=[c for c in checks if c['mandatory']]
    passing=sum(c['status']=='provided_unverified' for c in required)
    return {'name':'Required-field screening score','score':round(100*passing/len(required)) if required else None,
            'requirements_screened':len(required),'fields_matching_rules':passing,'disclaimer':SCREENING_NOTICE,
            'meaning':'Completeness against loaded machine-readable rules; document authenticity and substantive compliance are not verified.'}
