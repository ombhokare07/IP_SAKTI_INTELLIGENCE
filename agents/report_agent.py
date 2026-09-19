from agents.base import RAGAgent
class ReportAgent(RAGAgent):
    name='report'
    def run(self,payload):
        # Explicit report creation through the report API supplies an already-computed assessment.
        assessment=payload.get('assessment')
        if not assessment:
            return {'status':'input_required','answer':'Run a screening task, then create a report from its result.','citations':[]}
        return self.services.reports.create(payload.get('title','Screening report'),payload.get('kind','screening'),assessment)
