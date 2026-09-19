from intelligence.trust.contradiction_detector import detect_contradictions
class ContradictionAgent:
    name='contradiction'
    def run(self,citations):
        # Cross-jurisdiction differences are not automatically contradictions.
        groups={}
        for c in citations:groups.setdefault(c.get('jurisdiction',c.get('agent','unknown')),[]).append({'text':c['excerpt'],'chunk_id':c['id']})
        findings=[detect_contradictions(group) for group in groups.values()]
        return {'detected':any(r['detected'] for r in findings),'groups':findings,
                'limitations':['Deterministic contradiction heuristics are incomplete; compare original source scope and dates.']}
