"""Extract claimed uses, without implying clinical efficacy."""
from intelligence.traditional_knowledge.extraction import extract_mentions
USES={
    'wound healing':['wound healing','heal wounds','wound treatment','घाव भरने','जखम भरणे'],
    'inflammation':['inflammation','anti-inflammatory','सूजन','दाह'],
    'digestion':['digestion','digestive','पाचन'],
    'cough':['cough','खांसी','खोकला'],
    'fever':['fever','बुखार','ताप'],
    'pain':['pain','दर्द','वेदना'],
    'diabetes':['diabetes','मधुमेह'],
    'skin care':['skin care','त्वचा'],
    'stress':['stress','तनाव','ताण'],
}
def extract_therapeutic_uses(text): return extract_mentions(text,USES)
class TherapeuticUseExtractor:
    extract=staticmethod(extract_therapeutic_uses)
