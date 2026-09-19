import copy
import json
from pathlib import Path
import pytest
from services.database_service import DatabaseService
from intelligence.regulations.models import RegulationVersion
from intelligence.regulations.providers import LocalRegulationProvider
from intelligence.regulations.version_tracker import VersionTracker
from intelligence.regulations.regulation_engine import RegulationEngine
from intelligence.regulations.regulation_diff import diff_regulations
from intelligence.regulations.impact_analyzer import analyze_impact
from intelligence.regulations.jurisdiction_engine import normalize_jurisdiction
from intelligence.compliance.compliance_checker import ComplianceChecker
from intelligence.compliance.journey_generator import ComplianceJourneyGenerator
from intelligence.compliance.missing_field_detector import extract_document_fields,is_missing
from intelligence.traditional_knowledge.tk_engine import TraditionalKnowledgeEngine
from intelligence.traditional_knowledge.providers import LocalTKProvider
from intelligence.traditional_knowledge.similarity_checker import extract_features
from services.provider_gateway import ProviderUnavailable
ROOT=Path(__file__).resolve().parents[2]

@pytest.fixture
def regulation(tmp_path):
 r=RegulationEngine(VersionTracker(DatabaseService(tmp_path/'db.sqlite')),LocalRegulationProvider(ROOT/'data/fixtures/regulations.json',mock=True))
 assert r.sync()['status']=='synchronized'
 return r

@pytest.mark.parametrize('value,code',[('India','IN'),('USA','US'),('GB','UK'),('EU','EU'),('united kingdom','UK')])
def test_jurisdiction_aliases(value,code):assert normalize_jurisdiction(value)==code

def test_unsupported_jurisdiction_rejected():
 with pytest.raises(ValueError):normalize_jurisdiction('CA')

def test_regulation_fixture_scope_and_empty_cells(regulation):
 r=regulation.compare({'jurisdictions':['IN','US','EU','UK'],'product_category':'herbal_product'})
 assert r['mode']=='mock' and all(r['coverage'].values())
 assert r['trust']['trust_score']==0
 row=next(r for r in r['rows'] if r['field']=='safety_summary')
 assert row['jurisdictions']['IN']==[] and row['jurisdictions']['EU']
 assert all(c['source_url'] is None for c in r['citations'])

def test_regulation_no_provider_no_definitive_result(tmp_path):
 engine=RegulationEngine(VersionTracker(DatabaseService(tmp_path/'db.sqlite')))
 r=engine.compare({'jurisdictions':['IN'],'product_category':'herbal_product'})
 assert r['status']=='insufficient_evidence' and r['rows']==[] and r['trust']['trust_score']==0
 assert engine.sync()['status']=='provider_not_configured'
 assert ComplianceChecker(engine).check({})['score']['score'] is None

def test_version_selection_uses_effective_dates_and_category(regulation):
 old=regulation.tracker.current('IN','herbal_product',as_of='2025-01-15',mode='mock')
 assert old[0]['version']=='fixture-1'
 assert regulation.tracker.current('IN','herbal_product',as_of='2024-12-31',mode='mock')==[]
 assert regulation.tracker.current('IN','medical_device',mode='mock')==[]
 assert regulation.tracker.current('IN','herbal_product',mode='live')==[]

def test_immutable_versions_and_repeat_sync(regulation):
 assert regulation.sync()['imported']==0
 v=copy.deepcopy(regulation.tracker.list()[0]);v['title']='changed'
 with pytest.raises(ValueError):regulation.tracker.add(RegulationVersion.model_validate(v))
 assert len(regulation.tracker.list())==8

def test_ungrounded_requirement_mapping_is_rejected(regulation):
 v=copy.deepcopy(regulation.tracker.list()[0]);v['requirements'][0]['source_excerpt']='Invented legal requirement'
 with pytest.raises(ValueError):RegulationVersion.model_validate(v)

def test_mismatched_regulatory_source_modes_rejected(regulation):
 v=copy.deepcopy(regulation.tracker.list()[0]);v['mode']='live'
 with pytest.raises(ValueError):RegulationVersion.model_validate(v)

def test_diff_added_requirement_and_impact(regulation):
 change=next(c for c in regulation.changes()['changes'] if c['jurisdiction']=='IN')
 assert [r['field'] for r in change['added']]==['batch_reference']
 assert '+Test submissions must include batch reference.' in change['text_diff']
 impact=analyze_impact(change,{})
 assert impact['legal_impact']=='undetermined' and impact['missing_affected_fields']==['batch_reference']

def test_diff_removed_and_changed_requirements(regulation):
 old=copy.deepcopy(regulation.tracker.list(jurisdiction='IN')[0]);new=copy.deepcopy(old)
 new['version']='modified';new['requirements']=new['requirements'][1:];new['requirements'][0]['mandatory']=False
 d=diff_regulations(old,new)
 assert len(d['removed'])==1 and len(d['changed'])==1
 new['jurisdiction']='US'
 with pytest.raises(ValueError):diff_regulations(old,new)

@pytest.mark.parametrize('value',[None,'','   ','unknown','N/A',[],{}])
def test_empty_assertions_are_missing(value):assert is_missing(value)

@pytest.mark.parametrize('value',[0,False,'Actual content'])
def test_nonempty_assertions_preserved(value):assert not is_missing(value)

def test_compliance_extracts_only_explicit_fields(regulation):
 text='Product name: Test item\nIngredients: turmeric\nWe have a manufacturer somewhere.'
 fields=extract_document_fields(text)
 assert fields=={'product_name':'Test item','ingredients':'turmeric'}
 r=ComplianceChecker(regulation).check({'document_text':text})
 assert set(r['missing_fields'])=={'manufacturer','batch_reference'}
 assert r['score']['score']==50 and r['legal_compliance']=='undetermined'
 assert r['trust']['trust_score']==0

def test_complete_fixture_fields_never_claim_legal_compliance(regulation):
 r=ComplianceChecker(regulation).check({'fields':{'product_name':'x','ingredients':'y','manufacturer':'z','batch_reference':'b'}})
 assert r['score']['score']==100 and all(c['status']=='provided_unverified' for c in r['checks'])
 assert r['legal_compliance']=='undetermined'

def test_journey_dependencies_are_acyclic_and_evidence_backed(regulation):
 r=ComplianceJourneyGenerator(ComplianceChecker(regulation)).generate({})
 visited=set()
 for step in r['steps']:
  assert set(step['depends_on'])<=visited
  visited.add(step['id'])
 assert r['steps'][-1]['id']=='professional_review'
 assert all(s['status']!='approved' for s in r['steps'])

def test_tk_extractors_handle_language_aliases_and_process_mentions():
 r=extract_features('हळद आणि कोरफड; turmeric decoction for wound healing')
 assert {i['canonical'] for i in r['ingredients']}=={'turmeric','aloe vera'}
 assert r['therapeutic_uses'][0]['canonical']=='wound healing'
 assert r['processes'][0]['canonical']=='decoction'

def test_tk_no_provider_retains_input_without_clearance():
 r=TraditionalKnowledgeEngine().assess({'description':'turmeric wound healing'})
 assert r['extracted']['ingredients'] and not r['search_performed']
 assert not r['tkdl_access'] and not r['risk']['final_clearance'] and r['risk']['score'] is None

def test_tk_mock_matches_link_to_actual_fixture_excerpt():
 engine=TraditionalKnowledgeEngine(LocalTKProvider(ROOT/'data/fixtures/tk.json',mock=True,authorized=True))
 r=engine.assess({'description':'turmeric and neem decoction for wound healing'})
 assert r['matches'][0]['similarity']['score']==100
 assert r['citations'][0]['mode']=='mock' and r['trust']['trust_score']==0
 assert not r['risk']['authorized_search_performed'] and not r['risk']['final_clearance']
 assert all(c['source_url'] is None and c['page'] is None for c in r['citations'])

def test_tk_no_match_never_means_clearance():
 engine=TraditionalKnowledgeEngine(LocalTKProvider(ROOT/'data/fixtures/tk.json',mock=True))
 r=engine.assess({'description':'novel mechanical semiconductor sensor'})
 assert r['matches']==[] and r['risk']['level']=='insufficient_evidence' and not r['risk']['final_clearance']

def test_tk_provider_failure_does_not_report_search_success():
 class Failed:
  mode='live';authorized=True
  def search(self,q):raise ProviderUnavailable('provider_authentication_failed')
 r=TraditionalKnowledgeEngine(Failed()).assess({'description':'neem'})
 assert not r['search_performed'] and r['status']=='provider_authentication_failed'
 assert not r['risk']['authorized_search_performed']

def test_synthetic_corpus_cannot_be_loaded_as_real():
 with pytest.raises(ProviderUnavailable):LocalTKProvider(ROOT/'data/fixtures/tk.json').search('x')
 with pytest.raises(ProviderUnavailable):LocalRegulationProvider(ROOT/'data/fixtures/regulations.json').versions()

def test_expired_latest_version_does_not_resurrect_superseded_version(regulation):
 old=copy.deepcopy(regulation.tracker.list(jurisdiction='IN')[-1])
 old['version']='fixture-3';old['effective_from']='2025-03-01';old['published_at']='2025-03-01';old['effective_to']='2025-04-01'
 regulation.tracker.add(RegulationVersion.model_validate(old))
 assert regulation.tracker.current('IN','herbal_product',as_of='2025-04-02',mode='mock')==[]
 assert regulation.tracker.current('IN','herbal_product',as_of='2025-02-15',mode='mock')[0]['version']=='fixture-2'

def test_ambiguous_same_date_versions_require_review(regulation):
 version=copy.deepcopy(regulation.tracker.list(jurisdiction='IN')[-1])
 version['version']='conflicting-version';version['title']='Alternative same-date snapshot'
 regulation.tracker.add(RegulationVersion.model_validate(version))
 assert regulation.tracker.current('IN','herbal_product',mode='mock')==[]

def test_negated_ingredient_is_not_positive_tk_overlap():
 r=extract_features('without turmeric, neem for wound healing')
 assert next(i for i in r['ingredients'] if i['canonical']=='turmeric')['negated']
 assert not next(i for i in r['ingredients'] if i['canonical']=='neem')['negated']
