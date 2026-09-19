from fastapi import APIRouter,Request
from backend.api.schemas.phase_schema import ComplianceRequest,ScreeningResponse
from backend.api.routes.common import services,compliance_payload,remember
router=APIRouter(prefix='/compliance',tags=['compliance'])
@router.post('/journey',response_model=ScreeningResponse)
def journey(payload:ComplianceRequest,request:Request):
    service=services(request)
    return remember(request,'journey',payload.model_dump(mode='json'),service.journey.generate(compliance_payload(payload,service)))
