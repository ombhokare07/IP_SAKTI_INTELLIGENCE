"""All OPS traffic uses httpx.MockTransport; no EPO credentials or real records."""
import httpx
import pytest
from intelligence.prior_art.providers.epo_ops_provider import EPOOPSProvider,parse_ops_xml
from intelligence.prior_art.providers.base import (
 PriorArtAuthenticationError,PriorArtConfigurationError,PriorArtMalformedResponseError,
 PriorArtProviderError,PriorArtRateLimitError,PriorArtTimeoutError)

XML=b'''<ops:world-patent-data xmlns:ops="http://ops.epo.org" xmlns="http://www.epo.org/exchange"><ops:biblio-search total-result-count="1"><ops:search-result><exchange-documents><exchange-document country="XX" doc-number="TEST001" kind="A1"><bibliographic-data><publication-reference><document-id document-id-type="docdb"><country>XX</country><doc-number>TEST001</doc-number><kind>A1</kind><date>20240102</date></document-id></publication-reference><application-reference><document-id><date>20230101</date></document-id></application-reference><priority-claims><priority-claim><document-id><date>20221201</date></document-id></priority-claim></priority-claims><parties><applicants><applicant data-format="epodoc"><applicant-name><name>SYNTHETIC TEST APPLICANT</name></applicant-name></applicant></applicants></parties><invention-title lang="de">TEST DE</invention-title><invention-title lang="en">SYNTHETIC TEST TITLE</invention-title><classification-ipc><text>A61K 00/00</text></classification-ipc></bibliographic-data><abstract lang="en"><p>Synthetic <b>turmeric</b> test only.</p></abstract></exchange-document></exchange-documents></ops:search-result></ops:biblio-search></ops:world-patent-data>'''
EMPTY=b'<world-patent-data><biblio-search total-result-count="0"/></world-patent-data>'

def provider(handler,**kwargs):
 return EPOOPSProvider('test-key','test-secret',client=httpx.Client(transport=httpx.MockTransport(handler)),**kwargs)
def token():return httpx.Response(200,json={'access_token':'test-token','expires_in':'1199','token_type':'Bearer'})

def test_ops_normalization_preserves_only_returned_metadata():
 r=parse_ops_xml(XML)[0]
 assert r.publication_number=='XXTEST001A1'
 assert r.title=='SYNTHETIC TEST TITLE' and r.abstract=='Synthetic turmeric test only.'
 assert r.publication_date=='2024-01-02' and r.filing_date=='2023-01-01' and r.priority_date=='2022-12-01'
 assert r.applicants==['SYNTHETIC TEST APPLICANT']
 assert r.claims==[] and r.source_url is None

def test_ops_client_credentials_and_token_cache():
 calls=[]
 def handler(request):
  calls.append(request)
  if request.url.path.endswith('accesstoken'):
   assert request.headers['Authorization'].startswith('Basic ')
   assert request.content==b'grant_type=client_credentials'
   return token()
  assert request.headers['Authorization']=='Bearer test-token'
  assert request.headers['X-OPS-Range']=='1-7'
  assert request.url.params['q']=='ta="turmeric" AND ta="extraction"'
  return httpx.Response(200,content=XML)
 p=provider(handler)
 assert p.search('turmeric extraction',7)[0].publication_number=='XXTEST001A1'
 p.search('turmeric extraction',7)
 assert len(calls)==3
 assert all('test-secret' not in str(c.url) for c in calls)

def test_ops_renews_expired_token_with_injected_clock():
 clock=[0.0];tokens=[]
 def handler(request):
  if request.url.path.endswith('accesstoken'):tokens.append(1);return token()
  return httpx.Response(200,content=EMPTY)
 p=provider(handler,clock=lambda:clock[0]);p.search('herb');clock[0]=1300;p.search('herb')
 assert len(tokens)==2

def test_ops_retries_401_only_once():
 searches=[];tokens=[]
 def handler(request):
  if request.url.path.endswith('accesstoken'):tokens.append(1);return token()
  searches.append(1);return httpx.Response(401)
 with pytest.raises(PriorArtAuthenticationError):provider(handler).search('herb')
 assert len(searches)==len(tokens)==2

def test_ops_recovers_after_one_401():
 searches=[]
 def handler(request):
  if request.url.path.endswith('accesstoken'):return token()
  searches.append(1);return httpx.Response(401) if len(searches)==1 else httpx.Response(200,content=EMPTY)
 assert provider(handler).search('herb')==[]

@pytest.mark.parametrize('status,error',[(403,PriorArtAuthenticationError),(429,PriorArtRateLimitError),(500,PriorArtProviderError),(302,PriorArtProviderError)])
def test_ops_controlled_error_statuses(status,error):
 def handler(request):
  return token() if request.url.path.endswith('accesstoken') else httpx.Response(status,text='SECRET response body')
 with pytest.raises(error) as e:provider(handler).search('herb')
 assert 'SECRET' not in str(e.value)

@pytest.mark.parametrize('payload',[{}, {'access_token':'','expires_in':'1200'}, {'access_token':'a','expires_in':'nan'}, {'access_token':'a','expires_in':-1}, {'access_token':'a','expires_in':30,'token_type':'Basic'},[]])
def test_ops_invalid_oauth_payloads(payload):
 with pytest.raises(PriorArtMalformedResponseError):provider(lambda _:httpx.Response(200,json=payload)).search('herb')

def test_ops_missing_credentials_never_calls_transport():
 client=httpx.Client(transport=httpx.MockTransport(lambda _:pytest.fail('Network must not be attempted')))
 with pytest.raises(PriorArtConfigurationError):EPOOPSProvider(client=client).search('herb')

@pytest.mark.parametrize('content',[b'<broken',b'<html>error</html>',b'<!DOCTYPE a [<!ENTITY x "payload">]><a/>',b'<root><biblio-search total-result-count="2"/></root>',b'<root><exchange-document/></root>'])
def test_ops_rejects_malformed_and_non_search_xml(content):
 with pytest.raises(PriorArtMalformedResponseError):parse_ops_xml(content)

def test_ops_timeout_controlled():
 def fail(request):raise httpx.ReadTimeout('SECRET')
 with pytest.raises(PriorArtTimeoutError) as e:provider(fail).search('herb')
 assert 'SECRET' not in str(e.value)

@pytest.mark.parametrize('query,limit',[('',1),('x',0),('x',101),('!!!',10)])
def test_ops_invalid_search_inputs(query,limit):
 with pytest.raises(ValueError):provider(lambda _:pytest.fail('No request')).search(query,limit)
