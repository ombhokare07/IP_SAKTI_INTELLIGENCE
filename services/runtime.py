"""Independent phase services: starting the offline app never needs a cloud key."""
from pathlib import Path
from services.database_service import DatabaseService
from services.document_service import DocumentService
from services.report_service import ReportService
from services.notification_service import NotificationService
from services.provider_gateway import JSONGateway
from services.speech_to_text import SpeechToTextService
from services.text_to_speech import TextToSpeechService
from multilingual.translator import Translator
from intelligence.traditional_knowledge.providers import LocalTKProvider,GatewayTKProvider
from intelligence.traditional_knowledge.tk_engine import TraditionalKnowledgeEngine
from intelligence.regulations.providers import LocalRegulationProvider,GatewayRegulationProvider
from intelligence.regulations.version_tracker import VersionTracker
from intelligence.regulations.regulation_engine import RegulationEngine
from intelligence.compliance.compliance_checker import ComplianceChecker
from intelligence.compliance.journey_generator import ComplianceJourneyGenerator

ROOT=Path(__file__).resolve().parents[1]
class Services:
    def __init__(self,settings):
        self.settings=settings
        self.db=DatabaseService(settings.app_data_dir/'ip_sakti.sqlite3')
        self.documents=DocumentService(self.db,settings.app_data_dir/'documents')
        self.reports=ReportService(self.db)
        self.gateways=[]
        self.configuration_errors=[]
        def gateway(url,key):
            try:g=JSONGateway(url,key.get_secret_value(),timeout=settings.provider_timeout)
            except ValueError:
                self.configuration_errors.append('A gateway URL is invalid. Use HTTPS without embedded credentials.')
                g=JSONGateway('','',timeout=settings.provider_timeout)
            self.gateways.append(g);return g
        allow_mock=settings.allow_mock_data and settings.app_env.casefold()!='production'
        for field, allowed in (
            ('tk_provider',{'','local','mock','http_json'}),
            ('regulation_provider',{'','local','mock','http_json'}),
            ('translation_provider',{'','http_json'}),('stt_provider',{'','http_json'}),('tts_provider',{'','http_json'})):
            if getattr(settings,field) not in allowed:
                self.configuration_errors.append(f'Unsupported {field}; this provider is unavailable.')
        if not allow_mock and (settings.tk_provider=='mock' or settings.regulation_provider=='mock'):
            self.configuration_errors.append('Mock providers require ALLOW_MOCK_DATA=true and a non-production environment.')
        tk=None
        if settings.tk_provider=='mock' and allow_mock:tk=LocalTKProvider(ROOT/'data/fixtures/tk.json',mock=True)
        elif settings.tk_provider=='local' and settings.tk_corpus_path:tk=LocalTKProvider(settings.tk_corpus_path,authorized=settings.tk_search_authorized)
        elif settings.tk_provider=='http_json':tk=GatewayTKProvider(gateway(settings.tk_api_url,settings.tk_api_key),authorized=settings.tk_search_authorized)
        self.tk=TraditionalKnowledgeEngine(tk)
        reg=None
        if settings.regulation_provider=='mock' and allow_mock:reg=LocalRegulationProvider(ROOT/'data/fixtures/regulations.json',mock=True)
        elif settings.regulation_provider=='local' and settings.regulation_corpus_path:reg=LocalRegulationProvider(settings.regulation_corpus_path)
        elif settings.regulation_provider=='http_json':reg=GatewayRegulationProvider(gateway(settings.regulation_api_url,settings.regulation_api_key))
        self.regulations=RegulationEngine(VersionTracker(self.db),reg)
        if reg and reg.mode in {'mock','local'}:self.regulations.sync()
        self.compliance=ComplianceChecker(self.regulations)
        self.journey=ComplianceJourneyGenerator(self.compliance)
        self.alerts=NotificationService(self.regulations,self.db)
        self.translator=Translator(gateway(settings.translation_api_url,settings.translation_api_key) if settings.translation_provider=='http_json' else None)
        self.stt=SpeechToTextService(gateway(settings.stt_api_url,settings.stt_api_key) if settings.stt_provider=='http_json' else None)
        self.tts=TextToSpeechService(gateway(settings.tts_api_url,settings.tts_api_key) if settings.tts_provider=='http_json' else None)
    def close(self):
        for gateway in self.gateways:gateway.close()
