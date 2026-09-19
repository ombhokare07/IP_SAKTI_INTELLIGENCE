"""Requirements are grounded in curated source excerpts; free prose is not guessed."""
from intelligence.regulations.models import RegulationVersion

def extract_requirements(versions):
    result=[]
    for raw in versions:
        v=RegulationVersion.model_validate(raw)
        for r in v.requirements:
            result.append({**r.model_dump(),'regulation_id':v.regulation_id,'version':v.version,'evidence_id':v.evidence.id})
    return result
class RequirementExtractor:
    extract=staticmethod(extract_requirements)
