from fastapi import APIRouter,Request,HTTPException
from pydantic import BaseModel,Field
from backend.api.routes.common import services
from intelligence.regulations.regulation_diff import diff_regulations
from intelligence.regulations.impact_analyzer import analyze_impact
router=APIRouter(prefix='/regulations',tags=['regulation-changes'])
class DiffRequest(BaseModel):
    regulation_id:str=Field(min_length=1,max_length=120)
    from_version:str=Field(min_length=1,max_length=120)
    to_version:str=Field(min_length=1,max_length=120)
    fields:dict=Field(default_factory=dict,max_length=200)
@router.get('/changes')
def changes(request:Request):return services(request).regulations.changes()
@router.post('/diff')
def diff(payload:DiffRequest,request:Request):
    reg=services(request).regulations
    versions={v['version']:v for v in reg.tracker.list(mode=reg.mode) if v['regulation_id']==payload.regulation_id}
    if payload.from_version not in versions or payload.to_version not in versions:raise HTTPException(404,'Stored regulation version not found.')
    result=diff_regulations(versions[payload.from_version],versions[payload.to_version])
    return {**result,'impact':analyze_impact(result,payload.fields)}
