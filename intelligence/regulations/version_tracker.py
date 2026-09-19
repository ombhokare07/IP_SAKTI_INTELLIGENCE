"""Immutable, content-addressed regulation snapshots, separated by provenance mode."""
import hashlib
import json
from datetime import date
from intelligence.regulations.models import RegulationVersion

class VersionTracker:
    def __init__(self,database):self.db=database
    def add(self,version: RegulationVersion):
        data=version.model_dump(mode='json')
        # Retrieval time is observational metadata; it must not create a new legal version.
        data['evidence'].pop('retrieved_at',None)
        digest=hashlib.sha256(json.dumps(data,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
        data['content_hash']=digest
        identifier=json.dumps([version.mode,version.regulation_id,version.version])
        return self.db.put('regulation_version',identifier,data,immutable=True)
    def list(self,*,mode=None,jurisdiction=None):
        return sorted([v for v in self.db.list('regulation_version') if (mode is None or v['mode']==mode) and (jurisdiction is None or v['jurisdiction']==jurisdiction)],
                      key=lambda v:(v['regulation_id'],v['effective_from'],v['published_at'],v['version']))
    def current(self,jurisdiction,category,*,as_of=None,mode=None):
        as_of=as_of or date.today().isoformat()
        selected={}
        ambiguous=set()
        for v in self.list(mode=mode,jurisdiction=jurisdiction):
            if v['product_category'] not in {category,'*'} or v['effective_from']>as_of or v['published_at']>as_of:continue
            key=v['regulation_id']
            chronology=(v['effective_from'],v['published_at'])
            if key not in selected or chronology>(selected[key]['effective_from'],selected[key]['published_at']):
                selected[key]=v
                ambiguous.discard(key)
            elif chronology==(selected[key]['effective_from'],selected[key]['published_at']) and v['version']!=selected[key]['version']:
                ambiguous.add(key)
        # Expiry of the latest applicable version must never resurrect an earlier version.
        return [v for k,v in selected.items() if k not in ambiguous and not (v['effective_to'] and as_of>v['effective_to'])]
