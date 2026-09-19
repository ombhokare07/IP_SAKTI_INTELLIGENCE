from agents.base import RAGAgent
class InternationalRegulationAgent(RAGAgent):
    name='international'
    def run(self,payload):
        result=self.services.regulations.compare(payload)
        return {**result,'answer':'Compare the source-backed requirement rows and jurisdiction coverage. Empty cells indicate missing evidence.'}
InternationalAgent=InternationalRegulationAgent
