from agents.base import RAGAgent
class TraditionalKnowledgeAgent(RAGAgent):
    name='traditional_knowledge'
    def run(self,payload):
        result=self.services.tk.assess({**payload,'description':payload.get('description') or payload['question']})
        return {**result,'answer':result['risk']['conclusion']}
