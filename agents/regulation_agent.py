from agents.international_agent import InternationalRegulationAgent
class RegulationAgent(InternationalRegulationAgent):
    name='regulation'
    def run(self,payload):
        return super().run({**payload,'jurisdictions':[payload.get('jurisdiction','IN')]})
