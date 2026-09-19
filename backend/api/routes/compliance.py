from fastapi import APIRouter,Request
from backend.api.schemas.phase_schema import ComplianceRequest,ScreeningResponse
from backend.api.routes.common import services,compliance_payload,remember
router=APIRouter(prefix='/compliance',tags=['compliance'])
@router.post('/check',response_model=ScreeningResponse)
def check(payload:ComplianceRequest,request:Request):
    service=services(request)
    return remember(request,'compliance',payload.model_dump(mode='json'),service.compliance.check(compliance_payload(payload,service)))
