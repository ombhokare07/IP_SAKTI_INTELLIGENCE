"""Speech-to-text gateway contract; missing providers never invent a transcript."""
import base64
from typing import Protocol
from services.provider_gateway import ProviderUnavailable

class SpeechToTextAdapter(Protocol):
    def transcribe(self, audio: bytes, language: str, mime_type: str) -> dict: ...

class SpeechToTextService:
    def __init__(self, gateway=None): self.gateway=gateway
    def transcribe(self,audio: bytes,language='en',mime_type='audio/webm'):
        if language not in {'en','hi','mr'} or mime_type not in {'audio/webm','audio/wav','audio/mpeg','audio/ogg'} or not 0<len(audio)<=5_000_000:
            raise ValueError('Use supported audio up to 5 MB and language en, hi or mr.')
        if not self.gateway or not self.gateway.configured:
            return {'status':'unconfigured','mode':'unconfigured','transcript':None,'language':language,'message':'Speech recognition is unavailable. Type your question.'}
        try:
            r=self.gateway.call({'operation':'transcribe','audio_base64':base64.b64encode(audio).decode(),'language':language,'mime_type':mime_type})
            if not isinstance(r.get('transcript'),str) or not r['transcript'].strip() or len(r['transcript'])>20_000:
                raise ProviderUnavailable('provider_malformed_response')
            return {'status':'transcribed','mode':'live','transcript':r['transcript'],'language':language}
        except ProviderUnavailable as e:
            return {'status':e.code,'mode':'live','transcript':None,'language':language,'message':'Speech recognition failed. Type your question.'}
