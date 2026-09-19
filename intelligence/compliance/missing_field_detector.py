import re

def extract_document_fields(text: str) -> dict:
    """Read explicit Label: value lines. Never infer absent facts from prose."""
    fields={}
    for line in text.splitlines():
        match=re.match(r'^\s*([A-Za-z][A-Za-z0-9 _-]{0,79})\s*:\s*(.+?)\s*$',line)
        if match:
            key=re.sub(r'[^a-z0-9]+','_',match[1].lower()).strip('_')
            fields.setdefault(key,match[2])
    return fields

def is_missing(value):
    return value is None or isinstance(value,str) and (not value.strip() or value.strip().lower() in {'n/a','unknown','not provided','none','null'}) or isinstance(value,(list,dict)) and not value

def detect_missing_fields(requirements,fields):
    return sorted({r['field'] for r in requirements if r['mandatory'] and is_missing(fields.get(r['field']))})
class MissingFieldDetector:
    detect=staticmethod(detect_missing_fields)
