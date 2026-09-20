from agents.base import RAGAgent,unconfigured
from intelligence.patentability.invention_analyzer import InventionAnalyzer
class PriorArtAgent(RAGAgent):
    name='prior_art'
    def run(self,payload):
        engine=getattr(self.state,'prior_art_engine',None)
        if not engine:
            return {**unconfigured('No real prior-art search is configured. No final novelty conclusion can be made.'),
                    'limitations':['NO REAL PRIOR-ART SEARCH -> NO FINAL NOVELTY CLAIM.',
                                   'No records were evaluated because no prior-art provider is configured.']}
        invention=InventionAnalyzer().analyze({'title':payload.get('title') or 'User invention','description':payload.get('description') or payload['question'],**{k:v for k,v in payload.items() if k in ('ingredients','process','claimed_innovation','technical_advantage')}})
        result=engine.search(invention,limit=payload.get('limit',10))
        mode=result['search_summary']['provider_mode']
        citations=[{'id':r.get('publication_number'),'title':r.get('title'),'excerpt':r.get('abstract') or r.get('title'),
                    'source_url':r.get('source_url'),'locator':r.get('publication_number'),'mode':mode} for r in result['results'] if r.get('publication_number')]
        return {**result,'mode':mode,'citations':citations,'answer':'A limited prior-art search was performed. Detected overlaps are screening leads; this does not establish novelty.'}
