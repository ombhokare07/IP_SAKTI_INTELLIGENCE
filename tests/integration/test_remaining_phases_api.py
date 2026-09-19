"""Offline API workflows for phases 2C–7. No credentialed network calls."""
import base64
from pathlib import Path
from types import SimpleNamespace
import pytest
from fastapi.testclient import TestClient
from config.settings import Settings
from backend.main import create_app
from agents.intent_classifier import IntentClassifier
from agents.orchestrator import Orchestrator
from agents.contradiction_agent import ContradictionAgent

@pytest.fixture
def settings(tmp_path):
 return Settings(_env_file=None,gemini_api_key='',app_data_dir=tmp_path/'runtime',vector_db_path=tmp_path/'vectors',
                 allow_mock_data=True,tk_provider='mock',regulation_provider='mock',
                 prior_art_provider='mock',prior_art_allow_mock=True)
@pytest.fixture
def client(settings):
 with TestClient(create_app(settings)) as c:yield c

def test_startup_without_cloud_key_initializes_independent_modules(client):
 r=client.get('/api/status')
 assert r.status_code==200
 data=r.json()
 assert data['providers']['rag']=='unconfigured'
 assert data['providers']['traditional_knowledge']=='mock' and data['providers']['regulations']=='mock'
 assert data['providers']['prior_art']=='mock' and not data['tkdl_access']

@pytest.mark.parametrize('endpoint,body',[('/traditional-knowledge/assess',{'description':'turmeric and neem decoction for wound healing'}),('/regulations/compare',{}),('/compliance/check',{}),('/compliance/journey',{})])
def test_offline_phase_endpoints_return_explicit_mock_mode(client,endpoint,body):
 r=client.post('/api'+endpoint,json=body)
 assert r.status_code==200 and r.json()['mode']=='mock'

def test_independent_prior_art_mock_does_not_download_embedding_model(client):
 r=client.post('/api/prior-art/search',json={'title':'turmeric wound preparation','description':'turmeric and neem formulation for wound healing'})
 assert r.status_code==200 and r.json()['search_summary']['provider_mode']=='mock'
 assert all(p['publication_number'].startswith('TEST-FIXTURE-') for p in r.json()['results'])

def test_offline_patent_screen_keeps_original_no_evidence_rules(client):
 r=client.post('/api/patentability/screen',json={'title':'New formulation','description':'Turmeric formulation for wound healing'})
 assert r.status_code==200
 assert r.json()['assessment']['novelty']['status']=='insufficient_evidence'
 assert 'prior-art search' in r.json()['evidence_gaps']
 assert r.json()['trust']['evidence_score']==0

@pytest.mark.parametrize('question,intent',[('search prior art for a patent','prior_art'),('TKDL traditional knowledge','traditional_knowledge'),('compare EU UK rules','international'),('check compliance document','compliance'),('patentability of my formula','patent'),('an unrelated query','ask')])
def test_deterministic_intent_routing(question,intent):
 r=IntentClassifier().classify(question)
 assert r['primary']==intent
 assert len(r['intents'])<=4

def test_explicit_route_overrides_keywords():assert IntentClassifier().classify('patent','ayush')['primary']=='ayush'

@pytest.mark.parametrize('intent',['patent','ayush','prior_art','traditional_knowledge','international','regulation','compliance','ask'])
def test_agent_roles_run_and_keep_final_evidence_gate(client,intent):
 r=client.post('/api/agents/run',json={'question':'turmeric and neem decoction for wound healing','intent':intent})
 assert r.status_code==200
 body=r.json()
 assert intent in body['results']
 assert body['trace'][-1]['agent']=='contradiction'
 assert body['trust']['trust_score']==0
 assert body['status']=='insufficient_evidence'
 assert 'No reliable evidence' in body['answer']

def test_agent_provider_error_is_not_exposed_or_success(client):
 class Failing:
  def run(self,question):raise RuntimeError('PRIVATE API SECRET')
 client.app.state.rag_pipeline=Failing()
 r=client.post('/api/agents/run',json={'question':'arbitrary input','intent':'ask'})
 assert r.json()['status']=='agent_failed' and 'PRIVATE' not in r.text

def test_contradiction_agent_scopes_jurisdiction_differences():
 citations=[{'id':'1','excerpt':'Label is required.','jurisdiction':'IN'}, {'id':'2','excerpt':'Label is not required.','jurisdiction':'US'}]
 assert not ContradictionAgent().run(citations)['detected']
 citations[1]['jurisdiction']='IN'
 assert ContradictionAgent().run(citations)['detected']

def test_voice_pipeline_no_provider_does_not_call_agents(client):
 r=client.post('/api/voice/query',json={'audio_base64':base64.b64encode(b'audio').decode(),'language':'hi'})
 assert r.status_code==200 and r.json()['speech']['status']=='unconfigured'
 assert r.json()['assessment'] is None and r.json()['audio'] is None

def test_multilingual_api_offline_fallback(client):
 r=client.post('/api/languages/translate',json={'text':'Unusual source passage [2].','source_language':'en','target_language':'mr'})
 assert r.status_code==200 and not r.json()['translated'] and r.json()['output_language']=='en'

@pytest.mark.parametrize('path,body',[('/traditional-knowledge/assess',{'description':' '}),('/agents/run',{'question':''}),('/regulations/compare',{'jurisdictions':['CA']}),('/regulations/compare',{'jurisdictions':[]}),('/voice/synthesize',{'text':'x','language':'de'}),('/compliance/check',{'document_id':'../../file'}),('/regulations/compare',{'as_of':'not-a-date'}),('/agents/run',{'question':'x','intent':'arbitrary'}),('/traditional-knowledge/assess',{'description':'x','provider':'tkdl'})])
def test_new_api_validation_rejects_invalid_inputs(client,path,body):
 assert client.post('/api'+path,json=body).status_code==422

def test_document_upload_read_download_and_missing_document(client):
 contents=b'Product name: Offline test\nIngredients: turmeric'
 r=client.post('/api/documents',json={'name':'../../form.txt','content_base64':base64.b64encode(contents).decode()})
 assert r.status_code==201
 document=r.json();identifier=document['id']
 assert document['name']=='form.txt' and document['page_count'] is None and not document['source_verified']
 assert client.get('/api/documents').json()['documents'][0]['id']==identifier
 assert client.get('/api/documents/'+identifier+'/file').content==contents
 checked=client.post('/api/compliance/check',json={'document_id':identifier}).json()
 assert checked['fields']['product_name']=='Offline test'
 assert client.post('/api/compliance/check',json={'document_id':'a'*32}).status_code==404
 assert client.get('/api/documents/missing').status_code==404

@pytest.mark.parametrize('name,content',[('a.txt','!invalid!'),('a.exe',base64.b64encode(b'bad').decode()),('a.pdf',base64.b64encode(b'not pdf').decode())])
def test_document_malformed_inputs_do_not_succeed(client,name,content):
 assert client.post('/api/documents',json={'name':name,'content_base64':content}).status_code==422

def test_pdf_api_ingestion_uses_preserved_pipeline_with_offline_embedding(client,monkeypatch):
 import fitz
 import rag.embeddings.embedding_service as embeddings
 class Offline:
  def __init__(self,**kwargs):pass
  def embed_documents(self,texts,**kwargs):return [[1.0,0.0] for t in texts]
 monkeypatch.setattr(embeddings,'BGEEmbeddingService',Offline)
 with fitz.open() as pdf:
  p=pdf.new_page();p.insert_text((72,72),'Synthetic source for the offline integration test.')
  content=pdf.tobytes()
 record=client.post('/api/documents',json={'name':'test.pdf','content_base64':base64.b64encode(content).decode()}).json()
 assert record['pages'][0]['page']==1
 r=client.post('/api/documents/'+record['id']+'/ingest',json={})
 assert r.status_code==200 and r.json()['stored_chunks']==1 and r.json()['document']['rag_indexed']

@pytest.mark.parametrize('kind,input',[('traditional_knowledge',{'description':'neem decoction'}),('comparison',{}),('compliance',{}),('journey',{}),('changes',{}),('patent',{'title':'Test','description':'Turmeric formulation'}),('ask',{'question':'traditional knowledge neem','intent':'traditional_knowledge'})])
def test_report_generation_and_all_exports(client,kind,input):
 response=client.post('/api/reports',json={'title':'<script>unsafe title</script>','kind':kind,'input':input})
 assert response.status_code==201
 report=response.json()
 assert client.get('/api/reports/'+report['id']).json()['assessment']==report['assessment']
 for format in ['json','markdown','html']:
  result=client.get('/api/reports/'+report['id']+'/export',params={'format':format})
  assert result.status_code==200 and 'attachment;' in result.headers['content-disposition']
  if format=='html':assert '<script>unsafe title' not in result.text and '&lt;script&gt;' in result.text
 assert client.get('/api/reports/'+report['id']+'/export?format=unknown').status_code==422

def test_report_cannot_accept_invented_assessment(client):
 r=client.post('/api/reports',json={'kind':'patent','input':{'assessment':{'novel':True}}})
 assert r.status_code==422

def test_regulation_diff_and_alert_acknowledgement(client):
 r=client.post('/api/regulations/diff',json={'regulation_id':'REG-TEST-IN','from_version':'fixture-1','to_version':'fixture-2'})
 assert r.status_code==200 and r.json()['added'][0]['field']=='batch_reference'
 alerts=client.get('/api/alerts').json()['alerts']
 assert len(alerts)==4
 a=alerts[0]['id']
 assert client.post(f'/api/alerts/{a}/acknowledge',json={}).json()['acknowledged']
 assert any(x['id']==a and x['acknowledged'] for x in client.get('/api/alerts').json()['alerts'])
 assert client.post('/api/alerts/missing/acknowledge',json={}).status_code==404

def test_api_auth_and_cors(settings):
 settings.api_auth_required=True;settings.api_auth_token='test-api-token'
 # Assignment is explicit in this test; use SecretStr as production settings validation does.
 from pydantic import SecretStr
 settings.api_auth_token=SecretStr('test-api-token')
 with TestClient(create_app(settings)) as client:
  assert client.get('/health').status_code==200
  assert client.get('/api/status').status_code==401
  assert client.get('/api/status',headers={'Authorization':'Bearer wrong'}).status_code==401
  r=client.get('/api/status',headers={'Authorization':'Bearer test-api-token','Origin':'http://localhost:3000'})
  assert r.status_code==200 and r.headers['access-control-allow-origin']=='http://localhost:3000'
  assert 'test-api-token' not in r.text
  assert client.options('/api/status',headers={'Origin':'http://localhost:3000','Access-Control-Request-Method':'GET','Access-Control-Request-Headers':'authorization'}).status_code==200

def test_production_disables_all_mocks_and_requires_auth(settings):
 from pydantic import SecretStr
 settings.app_env='production';settings.api_auth_token=SecretStr('token')
 with TestClient(create_app(settings)) as client:
  assert client.get('/api/status').status_code==401
  r=client.get('/api/status',headers={'Authorization':'Bearer token'}).json()
  assert not any(v=='mock' for v in r['providers'].values())

def test_missing_production_auth_key_fails_gracefully(settings):
 settings.app_env='production'
 with TestClient(create_app(settings)) as client:
  assert client.get('/health').status_code==200
  assert client.get('/api/status').status_code==503

def test_epo_can_initialize_without_gemini_or_network(settings):
 from pydantic import SecretStr
 settings.prior_art_provider='epo_ops';settings.epo_ops_consumer_key=SecretStr('test');settings.epo_ops_consumer_secret=SecretStr('test')
 with TestClient(create_app(settings)) as client:
  assert client.app.state.prior_art_engine.provider.name=='epo_ops'
  assert client.get('/api/status').json()['providers']['prior_art']=='configured_not_verified'

def test_records_persist_across_application_restart(settings):
 with TestClient(create_app(settings)) as first:
  report=first.post('/api/reports',json={'kind':'comparison','input':{}}).json()
 with TestClient(create_app(settings)) as second:
  assert second.get('/api/reports/'+report['id']).status_code==200

def test_report_saves_exact_assessment_without_requery(client,monkeypatch):
 result=client.post('/api/traditional-knowledge/assess',json={'description':'turmeric and neem decoction for wound healing'}).json()
 monkeypatch.setattr(client.app.state.services.tk,'assess',lambda *_:pytest.fail('Saving must not rerun the assessment'))
 report=client.post('/api/reports',json={'kind':'traditional_knowledge','assessment_id':result['assessment_id']})
 assert report.status_code==201 and report.json()['assessment']==result
 assert client.post('/api/reports',json={'kind':'comparison','assessment_id':result['assessment_id']}).status_code==422

def test_report_unknown_snapshot_is_not_created(client):
 assert client.post('/api/reports',json={'kind':'compliance','assessment_id':'f'*32}).status_code==404

def test_translation_agent_reports_actual_fallback_language(client):
 r=client.post('/api/agents/run',json={'question':'Unusual legal source text [1].','intent':'translation','source_language':'en','target_language':'mr'})
 assert r.status_code==200 and r.json()['output_language']=='en'
 assert r.json()['status']=='translation_unavailable' and r.json()['answer']=='Unusual legal source text [1].'
