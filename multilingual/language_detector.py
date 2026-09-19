"""Offline heuristic detection; shared Devanagari without enough cues is ambiguous."""
import re

SUPPORTED = ('en', 'hi', 'mr')

def detect_language(text: str, hint: str | None = None) -> dict:
    if hint in SUPPORTED:
        return {'language':hint,'confidence':1.0,'method':'user_hint','ambiguous':False}
    if not text.strip():
        return {'language':'und','confidence':0.0,'method':'heuristic','ambiguous':True}
    dev = bool(re.search(r'[\u0900-\u097f]',text))
    if dev:
        marathi = re.findall(r'आहे|आहेत|माझ|मला|करा|साठी|काय|हळद|तुळस|कोरफड|मराठी',text)
        hindi = re.findall(r'है|हैं|मुझे|मेरा|करें|लिए|क्या|हल्दी|हिंदी',text)
        language = 'mr' if len(marathi)>len(hindi) else 'hi' if len(hindi)>len(marathi) else 'und'
        return {'language':language,'confidence':0.8 if language!='und' else 0.0,
                'method':'heuristic','ambiguous':language=='und','candidates':['hi','mr']}
    latin = bool(re.search(r'[A-Za-z]',text))
    return {'language':'en' if latin else 'und','confidence':0.6 if latin else 0.0,
            'method':'heuristic','ambiguous':not latin,
            'limitations':['Latin text is provisionally treated as English; romanized and mixed languages may need an explicit hint.']}

class LanguageDetector:
    detect = staticmethod(detect_language)
