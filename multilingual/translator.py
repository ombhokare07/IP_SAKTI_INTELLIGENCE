"""Translation with protected evidence tokens and honest offline fallback."""
import json
import re
from pathlib import Path
from multilingual.language_detector import SUPPORTED, detect_language
from services.provider_gateway import ProviderUnavailable

TOKEN = re.compile(r'https?://[^\s<>]+|\[\d+\]|\b\d+(?:[.,]\d+)*\b')

class Translator:
    def __init__(self, gateway=None):
        self.gateway = gateway
        self.phrases={lang:json.loads((Path(__file__).parent/'dictionaries'/f'{name}.json').read_text(encoding='utf-8'))
                      for lang,name in [('en','english'),('hi','hindi'),('mr','marathi')]}

    def translate(self, text: str, target: str = 'en', source: str | None = None) -> dict:
        if target not in SUPPORTED or (source is not None and source not in (*SUPPORTED,'und')):
            raise ValueError('Supported languages are en, hi and mr.')
        detected=detect_language(text,source)
        source=detected['language']
        result={'original_text':text,'text':text,'source_language':source,'target_language':target,
                'output_language':source,'translated':False,'mode':'local','status':'original',
                'detection':detected,'warnings':[]}
        if source == target:
            return result
        for lang,phrases in self.phrases.items():
            for key,value in phrases.items():
                if text == value:
                    return {**result,'text':self.phrases[target][key],'translated':True,
                            'output_language':target,'status':'dictionary_translation'}
        if not self.gateway or not self.gateway.configured or source=='und':
            return {**result,'status':'translation_unavailable','warnings':[
                'Original text retained. Configure a translation provider and supply a language hint when detection is ambiguous.']}
        protected=[]
        def mask(match):
            protected.append(match.group())
            return f'IPSAKTI_TOKEN_{len(protected)-1}_END'
        masked=TOKEN.sub(mask,text)
        try:
            response=self.gateway.call({'operation':'translate','text':masked,'source_language':source,'target_language':target})
            translated=response.get('text')
            if not isinstance(translated,str) or not translated.strip() or response.get('target_language')!=target:
                raise ProviderUnavailable('provider_malformed_response')
            expected={f'IPSAKTI_TOKEN_{i}_END' for i in range(len(protected))}
            actual=re.findall(r'IPSAKTI_TOKEN_\d+_END',translated)
            if set(actual)!=expected or len(actual)!=len(expected):
                raise ProviderUnavailable('translation_evidence_tokens_changed')
            for i,value in enumerate(protected):
                translated=translated.replace(f'IPSAKTI_TOKEN_{i}_END',value)
            return {**result,'text':translated,'translated':True,'output_language':target,'mode':'live',
                    'status':'translated','warnings':['Machine translation needs review; original evidence remains authoritative.']}
        except ProviderUnavailable as exc:
            return {**result,'status':exc.code,'warnings':['Translation failed; original text retained.']}
