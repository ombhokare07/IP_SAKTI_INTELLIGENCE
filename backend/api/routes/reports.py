from fastapi import APIRouter,Request,HTTPException
from fastapi.responses import Response
from pydantic import ValidationError
from backend.api.schemas.phase_schema import ReportRequest,TKRequest,CompareRequest,ComplianceRequest,AgentRequest
from backend.api.schemas.patent_schema import PatentabilityRequest
from backend.api.schemas.prior_art_schema import PriorArtSearchRequest
from backend.api.routes.common import services,compliance_payload
from backend.api.routes.agents import screen
from backend.api.routes.prior_art import search_prior_art
from agents.orchestrator import Orchestrator
from agents.report_agent import ReportAgent
router=APIRouter(prefix='/reports',tags=['reports'])
@router.get('')
def reports(request:Request):return {'reports':services(request).reports.list()}
@router.post('',status_code=201)
def create(payload:ReportRequest,request:Request):
    s=services(request)
    if payload.assessment_id:
        saved=s.db.get('assessment',payload.assessment_id)
        if not saved:raise HTTPException(404,'Assessment snapshot not found.')
        if saved['kind']!=payload.kind:raise HTTPException(422,'Report kind does not match the saved assessment.')
        return ReportAgent(s,request.app.state).run({'title':payload.title,'kind':payload.kind,'assessment':saved['result']})
    try:
        match payload.kind:
            case 'patent':result=screen(PatentabilityRequest.model_validate(payload.input),request)
            case 'prior_art':result=search_prior_art(PriorArtSearchRequest.model_validate(payload.input),request)
            case 'traditional_knowledge':result=s.tk.assess(TKRequest.model_validate(payload.input).model_dump())
            case 'comparison':result=s.regulations.compare(CompareRequest.model_validate(payload.input).model_dump(mode='json'))
            case 'compliance':result=s.compliance.check(compliance_payload(ComplianceRequest.model_validate(payload.input),s))
            case 'journey':result=s.journey.generate(compliance_payload(ComplianceRequest.model_validate(payload.input),s))
            case 'changes':result=s.regulations.changes()
            case 'ask':result=Orchestrator(s,request.app.state).run(AgentRequest.model_validate(payload.input).model_dump())
    except ValidationError:raise HTTPException(422,'Report input does not match the selected screening schema.')
    return ReportAgent(s,request.app.state).run({'title':payload.title,'kind':payload.kind,'assessment':result})
@router.get('/{identifier}')
def detail(identifier:str,request:Request):
    r=services(request).reports.get(identifier)
    if r is None:raise HTTPException(404,'Report not found.')
    return r
@router.get('/{identifier}/export')
def export(identifier:str,request:Request,format:str='json'):
    try:
        content,mime=services(request).reports.export(identifier,format)
        suffix={'json':'json','markdown':'md','html':'html'}[format]
        return Response(content,media_type=mime,headers={'Content-Disposition':f'attachment; filename="IP-SAKTI-report-{identifier}.{suffix}"','X-Content-Type-Options':'nosniff'})
    except KeyError:raise HTTPException(404,'Report not found.')
    except ValueError:raise HTTPException(422,'Use format=json, markdown or html.')
