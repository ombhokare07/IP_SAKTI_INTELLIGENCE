from intelligence.contracts import now_iso
from intelligence.regulations.comparator import compare_regulations
from intelligence.regulations.regulation_diff import diff_regulations
from intelligence.regulations.impact_analyzer import analyze_impact
from services.provider_gateway import ProviderUnavailable

class RegulationEngine:
    def __init__(self,tracker,provider=None):
        self.tracker,self.provider=tracker,provider
        self.mode=provider.mode if provider else 'unconfigured'
        self.sync_status={'status':'not_synchronized','mode':self.mode,'last_success':None}
    def sync(self):
        if not self.provider:return {'status':'provider_not_configured','mode':'unconfigured','imported':0}
        try:
            versions=self.provider.versions()
            # Preflight immutable conflicts before writing a batch.
            existing={(v['mode'],v['regulation_id'],v['version']):v for v in self.tracker.list()}
            seen={}
            import json
            for v in versions:
                key=(v.mode,v.regulation_id,v.version)
                d=v.model_dump(mode='json');d['evidence'].pop('retrieved_at',None)
                if key in seen and seen[key]!=d:raise ValueError('conflicting version')
                seen[key]=d
                if key in existing:
                    old=dict(existing[key]);old.pop('content_hash',None)
                    if old!=d:raise ValueError('conflicting version')
            imported=sum(self.tracker.add(v) for v in versions)
            self.sync_status={'status':'synchronized','mode':self.mode,'imported':imported,'last_success':now_iso()}
        except (ProviderUnavailable,ValueError) as e:
            self.sync_status={**self.sync_status,'status':getattr(e,'code','version_conflict'),'mode':self.mode,'imported':0,
                              'message':'Synchronization failed. Previously stored snapshots remain available and may be stale.'}
        return self.sync_status
    def compare(self,payload):
        result=compare_regulations(self.tracker,payload.get('jurisdictions',['IN','US','EU','UK']),payload.get('product_category','herbal_product'),mode=self.mode,as_of=payload.get('as_of'))
        return {**result,'sync':self.sync_status}
    def changes(self,jurisdiction=None):
        versions=self.tracker.list(mode=self.mode,jurisdiction=jurisdiction) if self.provider else []
        groups={}
        for v in versions:groups.setdefault(v['regulation_id'],[]).append(v)
        changes=[]
        for records in groups.values():
            for old,new in zip(records,records[1:]):
                diff=diff_regulations(old,new)
                if diff['added'] or diff['removed'] or diff['changed'] or diff['text_diff'] or diff['metadata_changes']:
                    diff['impact']=analyze_impact(diff)
                    changes.append(diff)
        return {'status':'available' if changes else 'no_stored_changes','mode':self.mode,'changes':changes,'sync':self.sync_status,
                'limitations':['Only synchronized snapshots are compared. No continuous monitoring or live-feed success is implied.']}
