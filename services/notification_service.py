"""In-app regulatory alerts derived exclusively from stored changes. No messaging."""
class NotificationService:
    def __init__(self,regulations,database):self.regulations,self.db=regulations,database
    def list(self):
        import hashlib
        changes=self.regulations.changes()
        alerts=[]
        for change in changes['changes']:
            identifier=hashlib.sha256(f'{change["mode"]}:{change["regulation_id"]}:{change["from_version"]}:{change["to_version"]}'.encode()).hexdigest()[:24]
            alerts.append({'id':identifier,'title':f'{change["regulation_id"]}: {change["from_version"]} → {change["to_version"]}',
                           'jurisdiction':change['jurisdiction'],'mode':change['mode'],'effective_from':change['effective_from'],
                           'impact':change['impact'],'acknowledged':bool(self.db.get('alert_ack',identifier))})
        return {'status':changes['status'],'mode':changes['mode'],'alerts':alerts,'sync':changes['sync']}
    def acknowledge(self,identifier):
        if not any(a['id']==identifier for a in self.list()['alerts']):raise KeyError(identifier)
        self.db.put('alert_ack',identifier,{'acknowledged':True})
        return {'id':identifier,'acknowledged':True}
