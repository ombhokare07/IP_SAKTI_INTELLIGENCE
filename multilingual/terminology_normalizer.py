"""Versioned, deterministic terminology matching with input spans."""
import json
import re
import unicodedata
from pathlib import Path

DICTIONARY = json.loads((Path(__file__).parent / 'dictionaries/ayush_terms.json').read_text(encoding='utf-8'))

def match_terms(text: str) -> list[dict]:
    found = []
    for entry in DICTIONARY['terms']:
        for alias in sorted(set(entry['aliases']), key=len, reverse=True):
            match = re.search(r'(?<![\w\u0900-\u097f])'+re.escape(alias)+r'(?![\w\u0900-\u097f])',text,re.I)
            if match:
                found.append({'canonical':entry['canonical'],'botanical_candidate':entry['botanical'],
                              'original':match.group(),'start':match.start(),'end':match.end(),'method':'dictionary'})
                break
    return sorted(found,key=lambda x:x['start'])

def normalize_terminology(text: str) -> dict:
    text = unicodedata.normalize('NFC', text)
    matches = match_terms(text)
    normalized = text
    for match in reversed(matches):
        normalized=normalized[:match['start']]+match['canonical']+normalized[match['end']:]
    return {'original':text,'normalized':normalized,'terms':matches,'dictionary_version':DICTIONARY['version'],
            'limitations':[DICTIONARY['scope']]}

class TerminologyNormalizer:
    normalize = staticmethod(normalize_terminology)
