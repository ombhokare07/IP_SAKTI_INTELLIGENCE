from intelligence.contracts import now_iso, screening_trust
from intelligence.traditional_knowledge.similarity_checker import extract_features, compare_features
from intelligence.traditional_knowledge.risk_scorer import score_tk_risk
from services.provider_gateway import ProviderUnavailable

class TraditionalKnowledgeEngine:
    def __init__(self,provider=None):self.provider=provider
    def assess(self,payload: dict) -> dict:
        text=' '.join(str(payload.get(k) or '') for k in ('title','description','therapeutic_use','process'))
        text+=' '+', '.join(payload.get('ingredients') or [])
        if not text.strip():raise ValueError('Provide a description of the formulation or process.')
        features=extract_features(text)
        mode=self.provider.mode if self.provider else 'unconfigured'
        status='screened' if self.provider else 'provider_not_configured'
        searched=False
        records=[]
        try:
            if self.provider:
                records=self.provider.search(text)
                searched=True
        except ProviderUnavailable as e:status=e.code
        matches=[]
        for r in records:
            comparison=compare_features(features,extract_features(r.evidence.excerpt))
            if comparison['score']>0 and (r.evidence.locator or r.evidence.source_url):
                matches.append({'record_id':r.id,'similarity':comparison,'evidence':r.evidence.model_dump()})
        matches.sort(key=lambda m:(-m['similarity']['score'],m['record_id']))
        citations=[m['evidence'] for m in matches]
        return {'status':status,'mode':mode,'extracted':features,'search_performed':searched,
                'searched_at':now_iso() if searched else None,'records_examined':len(records),
                'tkdl_access':False,'matches':matches,'citations':citations,
                'risk':score_tk_risk(matches,searched=searched,authorized=bool(self.provider and self.provider.authorized),mode=mode),
                'trust':screening_trust(citations,mode=mode),
                'limitations':(['TEST DATA ONLY: synthetic corpus; not evidence of traditional knowledge.'] if mode=='mock' else [])+[
                    'NO AUTHORIZED TK SEARCH -> NO FINAL TK CLEARANCE.',
                    'No TKDL connection or authorization is bundled. A configured gateway searches only its operator-authorized corpus.',
                    'No matches do not establish absence of traditional knowledge. Extraction dictionaries are limited.']}
    check=assess
