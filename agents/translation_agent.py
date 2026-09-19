from agents.base import RAGAgent
class TranslationAgent(RAGAgent):
    name='translation'
    def run(self,payload):
        r=self.services.translator.translate(payload['question'],payload.get('target_language',payload.get('language','en')),payload.get('source_language'))
        return {**r,'answer':r['text'],'citations':[],'non_legal_operation':True}
