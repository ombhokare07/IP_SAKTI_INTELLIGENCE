from fastapi import APIRouter,Request
from backend.api.schemas.phase_schema import TKRequest,ScreeningResponse
from backend.api.routes.common import services,remember
router=APIRouter(prefix='/traditional-knowledge',tags=['traditional-knowledge'])
@router.post('/assess',response_model=ScreeningResponse)
def assess(payload:TKRequest,request:Request):return remember(request,'traditional_knowledge',payload.model_dump(),services(request).tk.assess(payload.model_dump()))
