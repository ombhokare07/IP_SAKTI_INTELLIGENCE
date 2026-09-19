from agents.base import RAGAgent
class ComplianceAgent(RAGAgent):
    name='compliance'
    def run(self,payload):
        result=self.services.compliance.check({**payload,'document_text':payload.get('document_text') or payload['question']})
        return {**result,'answer':'Document fields were screened against the loaded source requirements. Substantive legal compliance remains undetermined.'}
