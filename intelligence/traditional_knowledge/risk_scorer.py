from intelligence.contracts import SCREENING_NOTICE

def score_tk_risk(matches: list[dict],*,searched: bool,authorized: bool,mode: str) -> dict:
    score=max((m['similarity']['score'] for m in matches),default=0) if searched else None
    level='insufficient_evidence' if not matches else 'high_detected_overlap' if score>=70 else 'moderate_detected_overlap' if score>=35 else 'low_detected_overlap'
    return {'score':score,'level':level,'name':'Detected TK feature overlap','final_clearance':False,
            'authorized_search_performed':searched and authorized and mode!='mock',
            'conclusion':'Potential overlaps require expert review.' if matches else 'No evidence-backed TK conclusion can be made from this search.',
            'disclaimer':SCREENING_NOTICE}
class TKRiskScorer:
    score=staticmethod(score_tk_risk)
