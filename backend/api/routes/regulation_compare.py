from fastapi import APIRouter,Request
from backend.api.schemas.phase_schema import CompareRequest,ScreeningResponse
from backend.api.routes.common import services,remember
from intelligence.regulations.jurisdiction_engine import JurisdictionEngine
router=APIRouter(prefix='/regulations',tags=['regulations'])
@router.get('/jurisdictions')
def jurisdictions():return {'jurisdictions':JurisdictionEngine().list()}
@router.post('/compare',response_model=ScreeningResponse)
def compare(payload:CompareRequest,request:Request):return remember(request,'comparison',payload.model_dump(mode='json'),services(request).regulations.compare(payload.model_dump(mode='json')))
@router.post('/sync',response_model=ScreeningResponse)
def synchronize(request:Request):return services(request).regulations.sync()
@router.get('/versions')
def versions(request:Request):
    reg=services(request).regulations
    return {'mode':reg.mode,'versions':reg.tracker.list(mode=reg.mode) if reg.provider else [],'sync':reg.sync_status}
