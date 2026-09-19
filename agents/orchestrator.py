"""Bounded, deterministic orchestration. No autonomous credential or legal actions."""
from agents.intent_classifier import IntentClassifier
from agents.base import RAGAgent
from agents.patent_agent import PatentAgent
from agents.ayush_agent import AYUSHAgent
from agents.prior_art_agent import PriorArtAgent
from agents.traditional_knowledge_agent import TraditionalKnowledgeAgent
from agents.international_agent import InternationalRegulationAgent
from agents.regulation_agent import RegulationAgent
from agents.compliance_agent import ComplianceAgent
from agents.translation_agent import TranslationAgent
from agents.report_agent import ReportAgent
from agents.citation_agent import CitationAgent
from agents.evidence_agent import EvidenceAgent
from agents.contradiction_agent import ContradictionAgent
from intelligence.contracts import NO_EVIDENCE, SCREENING_NOTICE
from multilingual.terminology_normalizer import normalize_terminology

class Orchestrator:
    def __init__(self,services,state):
        self.services=services
        self.classifier=IntentClassifier()
        classes=[RAGAgent,PatentAgent,AYUSHAgent,PriorArtAgent,TraditionalKnowledgeAgent,InternationalRegulationAgent,RegulationAgent,ComplianceAgent,TranslationAgent,ReportAgent]
        self.agents={cls.name:cls(services,state) for cls in classes}
    def run(self,payload):
        question=payload.get('question','').strip()
        if not question:raise ValueError('Question is required.')
        language=payload.get('language','en')
        if payload.get('intent')=='translation':
            from intelligence.contracts import screening_trust
            translated=self.services.translator.translate(question,payload.get('target_language') or language,payload.get('source_language'))
            return {'question':question,'answer':translated['text'],'status':translated['status'],
                    'mode':translated['mode'],'output_language':translated['output_language'],
                    'routing':self.classifier.classify(question,'translation'),
                    'results':{'translation':translated},'citations':[],
                    'trust':screening_trust([],mode='unconfigured'),
                    'trace':[{'agent':'translation','status':translated['status']}],
                    'limitations':translated['warnings']}
        translation=self.services.translator.translate(question,'en',payload.get('source_language'))
        normalized=normalize_terminology(translation['text'])
        routing=self.classifier.classify(normalized['normalized'],payload.get('intent'))
        results={};trace=[]
        for intent in routing['intents']:
            try:
                result=self.agents[intent].run({**payload,'question':normalized['normalized']})
                status=result.get('status','screened')
            except Exception:
                # No provider exception body, user secret, or model output is exposed.
                result={'status':'agent_failed','answer':'The selected provider or processing step failed. No successful assessment is asserted.','citations':[],'mode':'unconfigured'}
                status='agent_failed'
            results[intent]=result
            trace.append({'agent':intent,'status':status})
        validated=CitationAgent().run(results)
        evidence=EvidenceAgent().run(validated['citations'],results)
        contradictions=ContradictionAgent().run(validated['citations'])
        answer='\n\n'.join(r.get('answer','Screening output is available below.') for r in results.values())
        status='screened'
        if not evidence['sufficient_for_screening'] and not all(r.get('non_legal_operation') for r in results.values()):
            answer=NO_EVIDENCE+'\n\n'+('Synthetic test output is shown for workflow demonstration only.' if evidence['mode']=='mock' else 'Review the task results for missing evidence or provider configuration.')
            status='insufficient_evidence'
        if contradictions['detected']:
            answer='Conflicting evidence was detected. Review the cited excerpts before relying on this screening.'
            status='conflicting_evidence'
            evidence['trust']['trust_score']=0
        if any(t['status']=='agent_failed' for t in trace):status='partial' if len(trace)>1 else 'agent_failed'
        output=self.services.translator.translate(answer,language,'en') if routing['primary']!='translation' else {'text':answer,'output_language':language,'status':'original'}
        return {'question':question,'answer':output['text'],'status':status,'mode':evidence['mode'],
                'output_language':output['output_language'],'routing':routing,'trace':trace+[{'agent':a,'status':'completed'} for a in ('citation','evidence','contradiction')],
                'results':results,'citations':validated['citations'],'rejected_citations':validated['rejected'],
                'trust':evidence['trust'],'contradictions':contradictions,'normalization':normalized,
                'input_translation':translation,'output_translation':output,
                'limitations':['NO EVIDENCE -> NO DEFINITIVE CONCLUSION.','NO REAL PRIOR-ART SEARCH -> NO FINAL NOVELTY CLAIM.','NO AUTHORIZED TK SEARCH -> NO FINAL TK CLEARANCE.',SCREENING_NOTICE]}
