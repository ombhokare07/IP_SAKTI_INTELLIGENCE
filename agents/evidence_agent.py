from intelligence.contracts import screening_trust
class EvidenceAgent:
    name='evidence'
    def run(self,citations,results):
        modes={c.get('mode','local') for c in citations}
        mode='mock' if 'mock' in modes else 'live' if 'live' in modes else 'local' if citations else 'unconfigured'
        real=[c for c in citations if c.get('mode')!='mock']
        ungrounded=any(r.get('trust',{}).get('unsupported_claims',0)>0 or r.get('trust',{}).get('hallucination_risk')=='high' for r in results.values())
        return {'mode':mode,'sufficient_for_screening':bool(real) and not ungrounded,
                'trust':screening_trust(citations,mode=mode,coverage=0 if ungrounded else 1),
                'unsupported_output_detected':ungrounded}
