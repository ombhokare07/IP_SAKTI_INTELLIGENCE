class EmptyRetriever:
    def retrieve(self,question):return []

def unconfigured(message):
    return {'status':'provider_not_configured','answer':message,'mode':'unconfigured','citations':[],
            'trust':{'trust_score':0,'evidence_score':0}}

class RAGAgent:
    name='ask'
    def __init__(self,services,state):self.services,self.state=services,state
    def run(self,payload):
        pipeline=getattr(self.state,'rag_pipeline',None)
        if not pipeline:return unconfigured('Grounded question answering is unavailable until a model and evidence corpus are configured.')
        return pipeline.run(payload['question'])
