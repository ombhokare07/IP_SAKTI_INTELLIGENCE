import base64
import httpx
import pytest
from multilingual.language_detector import detect_language
from multilingual.terminology_normalizer import normalize_terminology
from multilingual.translator import Translator
from services.provider_gateway import JSONGateway,ProviderUnavailable
from services.speech_to_text import SpeechToTextService
from services.text_to_speech import TextToSpeechService

@pytest.mark.parametrize('text,lang',[('Hello patent question','en'),('माझे उत्पादन काय आहे','mr'),('क्या यह हल्दी है','hi'),('अश्वगंधा','und'),('','und')])
def test_language_detection_with_ambiguous_devanagari(text,lang):assert detect_language(text)['language']==lang

def test_language_hint_and_dictionary_spans():
 assert detect_language('अश्वगंधा','mr')['language']=='mr'
 r=normalize_terminology('हळद आणि कोरफड')
 assert r['normalized']=='turmeric आणि aloe vera'
 assert all(r['original'][t['start']:t['end']]==t['original'] for t in r['terms'])

def test_terminology_does_not_match_substrings():assert normalize_terminology('turmericine and neemish')['terms']==[]

def test_offline_translation_preserves_untranslated_text():
 r=Translator().translate('An unusual legal analysis [1].','mr')
 assert not r['translated'] and r['text']=='An unusual legal analysis [1].' and r['output_language']=='en'
 assert r['status']=='translation_unavailable'

def test_offline_known_phrase_translation():
 r=Translator().translate('Insufficient reliable evidence was found in the current knowledge base.','hi','en')
 assert r['translated'] and r['output_language']=='hi' and r['mode']=='local'

class TranslateGateway:
 configured=True
 def __init__(self,break_tokens=False):self.break_tokens=break_tokens
 def call(self,p):return {'text':'अनुवाद '+(p['text'].replace('IPSAKTI_TOKEN_0_END','changed') if self.break_tokens else p['text']),'target_language':p['target_language']}

def test_translation_preserves_urls_numbers_and_citation_markers():
 original='Source [1] https://example.org/a requires 20 items.'
 r=Translator(TranslateGateway()).translate(original,'hi','en')
 assert r['translated'] and '[1]' in r['text'] and 'https://example.org/a' in r['text'] and '20' in r['text']
 assert r['mode']=='live'

def test_translation_rejects_lost_citation_marker():
 original='Source [1].'
 r=Translator(TranslateGateway(True)).translate(original,'hi','en')
 assert not r['translated'] and r['text']==original and r['status']=='translation_evidence_tokens_changed'

@pytest.mark.parametrize('url',['http://public.example','https://user:password@example.org','file:///etc/passwd','javascript:alert(1)'])
def test_gateway_rejects_unsafe_endpoints(url):
 with pytest.raises(ValueError):JSONGateway(url,'token')

def test_gateway_missing_auth_never_issues_network_request():
 g=JSONGateway('https://example.invalid','',client=httpx.Client(transport=httpx.MockTransport(lambda r:pytest.fail('Network attempt'))))
 with pytest.raises(ProviderUnavailable) as e:g.call({})
 assert e.value.code=='provider_not_configured'

@pytest.mark.parametrize('status,code',[(401,'provider_authentication_failed'),(403,'provider_authentication_failed'),(429,'provider_rate_limited'),(500,'provider_http_error'),(302,'provider_http_error')])
def test_gateway_failure_mapping(status,code):
 g=JSONGateway('https://example.invalid','TEST_SECRET',client=httpx.Client(transport=httpx.MockTransport(lambda r:httpx.Response(status,text='TEST_SECRET'))))
 with pytest.raises(ProviderUnavailable) as e:g.call({})
 assert e.value.code==code and 'TEST_SECRET' not in str(e.value)

@pytest.mark.parametrize('kind',['stt','tts'])
def test_voice_missing_provider_has_no_fabricated_output(kind):
 if kind=='stt':
  r=SpeechToTextService().transcribe(b'test audio','mr','audio/wav');assert r['transcript'] is None
 else:
  r=TextToSpeechService().synthesize('Hello','en');assert r['audio_base64'] is None
 assert r['status']=='unconfigured'

def test_voice_live_gateway_contract_with_offline_mock_transport():
 def handler(request):
  import json
  p=json.loads(request.content)
  if p['operation']=='transcribe':return httpx.Response(200,json={'transcript':'Test question'})
  return httpx.Response(200,json={'audio_base64':base64.b64encode(b'test audio').decode(),'mime_type':'audio/wav'})
 g=JSONGateway('https://example.invalid','test',client=httpx.Client(transport=httpx.MockTransport(handler)))
 assert SpeechToTextService(g).transcribe(b'123','hi','audio/wav')['transcript']=='Test question'
 assert TextToSpeechService(g).synthesize('test')['status']=='synthesized'

def test_tts_malformed_audio_is_not_success():
 class Gateway:
  configured=True
  def call(self,p):return {'audio_base64':'invalid%%%','mime_type':'audio/wav'}
 r=TextToSpeechService(Gateway()).synthesize('text')
 assert r['status']=='provider_failed' and r['audio_base64'] is None
