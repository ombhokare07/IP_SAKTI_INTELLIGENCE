from intelligence.contracts import SCREENING_NOTICE

def score_tk_risk(matches: list[dict],*,searched: bool,authorized: bool,mode: str) -> dict:
    score=max((m['similarity']['score'] for m in matches),default=0) if searched else None
    level='insufficient_evidence' if not matches else 'high_detected_overlap' if score>=70 else 'moderate_detected_overlap' if score>=35 else 'low_detected_overlap'
    authorized_search=searched and authorized and mode!='mock'
    return {'score':score,'level':level,'name':'Detected TK feature overlap','final_clearance':False,
            'authorized_search_performed':authorized_search,
            'matches_evaluated':searched,
            'clearance_status':'not_assessed' if not authorized_search else 'cannot_be_issued',
            'conclusion':(
                'Cannot be determined — authorized TK search not performed.' if not authorized_search
                else 'Potential overlaps require expert review.' if matches
                else 'No matches were found in the authorized configured source, but this does not establish absence of traditional knowledge.'
            ),
            'disclaimer':SCREENING_NOTICE}
class TKRiskScorer:
    score=staticmethod(score_tk_risk)
