import base64
import binascii
from fastapi import APIRouter,Request,HTTPException
from backend.api.schemas.phase_schema import STTRequest,TTSRequest
from backend.api.routes.common import services
from voice.voice_pipeline import VoicePipeline
from agents.orchestrator import Orchestrator
router=APIRouter(prefix='/voice',tags=['voice'])
def audio_bytes(payload):
    try:return base64.b64decode(payload.audio_base64,validate=True)
    except binascii.Error:raise HTTPException(422,'Invalid audio encoding.')
@router.post('/transcribe')
def transcribe(payload:STTRequest,request:Request):return services(request).stt.transcribe(audio_bytes(payload),payload.language,payload.mime_type)
@router.post('/synthesize')
def synthesize(payload:TTSRequest,request:Request):return services(request).tts.synthesize(payload.text,payload.language)
@router.post('/query')
def query(payload:STTRequest,request:Request):
    s=services(request)
    return VoicePipeline(s.stt,Orchestrator(s,request.app.state),s.tts).run(audio_bytes(payload),payload.language,payload.mime_type,payload.speak)
