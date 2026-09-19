from intelligence.traditional_knowledge.extraction import extract_mentions
PROCESSES={
 'extraction':['extraction','extracting','निष्कर्षण','अर्क काढणे'],
 'decoction':['decoction','काढ़ा','काढा','क्वाथ'],
 'boiling':['boiling','boiled','उबालना','उकळणे'],
 'fermentation':['fermentation','fermented','किण्वन'],
 'grinding':['grinding','ground powder','पीसना','दळणे'],
 'drying':['drying','dried','सुखाना','वाळवणे'],
 'distillation':['distillation','आसवन'],
 'filtration':['filtration','filtering','छानना','गाळणे'],
 'cold extraction':['cold extraction','low-temperature extraction','शीत निष्कर्षण'],
}
def extract_processes(text): return extract_mentions(text,PROCESSES)
class ProcessExtractor:
    extract=staticmethod(extract_processes)
