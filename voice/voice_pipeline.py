"""STT -> deterministic orchestration -> optional TTS. No hidden provider calls."""
class VoicePipeline:
    def __init__(self,stt,orchestrator,tts):
        self.stt,self.orchestrator,self.tts=stt,orchestrator,tts
    def run(self,audio: bytes,language='en',mime_type='audio/webm',speak=False):
        recognized=self.stt.transcribe(audio,language,mime_type)
        if recognized.get('transcript') is None:
            return {'speech':recognized,'assessment':None,'audio':None}
        result=self.orchestrator.run({'question':recognized['transcript'],'language':language})
        spoken=self.tts.synthesize(result['answer'],result.get('output_language','en')) if speak else None
        return {'speech':recognized,'assessment':result,'audio':spoken}
