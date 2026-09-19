from agents.base import RAGAgent,EmptyRetriever
from intelligence.patentability.patentability_engine import PatentabilityEngine
class PatentAgent(RAGAgent):
    name='patent'
    def run(self,payload):
        engine=getattr(self.state,'patentability_engine',None) or PatentabilityEngine(EmptyRetriever(),prior_art_engine=getattr(self.state,'prior_art_engine',None))
        result=engine.check({'title':payload.get('title') or 'User invention','description':payload.get('description') or payload['question'],**{k:v for k,v in payload.items() if k in ('ingredients','process','claimed_innovation','technical_advantage','run_prior_art_search')}})
        return {**result,'answer':'Preliminary patentability screening is available. Review evidence gaps and obtain an actual prior-art search before drawing a novelty conclusion.'}
