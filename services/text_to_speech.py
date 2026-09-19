"""Text-to-speech gateway with validated audio and text fallback."""
import base64
import binascii
from typing import Protocol
from services.provider_gateway import ProviderUnavailable

class TextToSpeechAdapter(Protocol):
    def synthesize(self,text: str,language: str) -> dict: ...

class TextToSpeechService:
    def __init__(self,gateway=None): self.gateway=gateway
    def synthesize(self,text,language='en'):
        if language not in {'en','hi','mr'} or not text.strip() or len(text)>20_000:
            raise ValueError('Use nonempty text up to 20000 characters and language en, hi or mr.')
        fallback={'text':text,'language':language,'audio_base64':None,'mime_type':None}
        if not self.gateway or not self.gateway.configured:
            return {**fallback,'status':'unconfigured','mode':'unconfigured','message':'Speech synthesis is unavailable. Read the text response.'}
        try:
            r=self.gateway.call({'operation':'synthesize','text':text,'language':language})
            audio=base64.b64decode(r.get('audio_base64',''),validate=True)
            if not 0<len(audio)<=5_000_000 or r.get('mime_type') not in {'audio/wav','audio/mpeg','audio/ogg','audio/webm'}:
                raise ValueError
            return {**fallback,'status':'synthesized','mode':'live','audio_base64':r['audio_base64'],'mime_type':r['mime_type']}
        except (ValueError,TypeError,binascii.Error,ProviderUnavailable):
            return {**fallback,'status':'provider_failed','mode':'live','message':'Speech synthesis failed. Read the text response.'}
