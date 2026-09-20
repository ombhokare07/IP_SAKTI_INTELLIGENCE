from intelligence.contracts import screening_trust,SCREENING_NOTICE,unique_strings
from intelligence.regulations.jurisdiction_engine import normalize_jurisdiction
from datetime import date

def compare_regulations(tracker,jurisdictions,product_category,*,mode,as_of=None):
    as_of=as_of or date.today().isoformat()
    countries=list(dict.fromkeys(normalize_jurisdiction(j) for j in jurisdictions))
    snapshots={j:tracker.current(j,product_category,mode=mode,as_of=as_of) for j in countries} if mode!='unconfigured' else {j:[] for j in countries}
    fields=sorted({r['field'] for versions in snapshots.values() for v in versions for r in v['requirements']})
    rows=[]
    for field in fields:
        cells={j:[{'requirement':r,'version':v['version'],'regulation_id':v['regulation_id'],'evidence_id':v['evidence']['id']} for v in snapshots[j] for r in v['requirements'] if r['field']==field] for j in countries}
        rows.append({'field':field,'jurisdictions':cells})
    citations=[{**v['evidence'],'jurisdiction':v['jurisdiction'],'regulation_id':v['regulation_id'],'version':v['version']} for versions in snapshots.values() for v in versions]
    coverage={j:bool(snapshots[j]) for j in countries}
    source_limitation=(
        'No configured regulatory evidence source was available for this jurisdiction. This does not mean no regulatory requirement applies.'
        if mode=='unconfigured' else
        'An empty cell means no requirement was found in the configured source; it does not mean no requirement applies.'
    )
    return {'status':'screened' if citations else 'insufficient_evidence','mode':mode,'product_category':product_category,
            'as_of':as_of,'jurisdictions':countries,'coverage':coverage,'rows':rows,'versions':snapshots,'citations':citations,
            'trust':screening_trust(citations,mode=mode,coverage=sum(coverage.values())/max(1,len(countries))),
            'limitations':unique_strings((['TEST DATA ONLY: synthetic regulation fixtures; no legal requirements are asserted.'] if mode=='mock' else [])+[
             source_limitation,
             'Expired or ambiguous version sets are excluded; missing coverage requires source review.',
             'Product classification, authority, source currency and jurisdiction coverage require professional verification.',SCREENING_NOTICE])}
class RegulationComparator:
    compare=staticmethod(compare_regulations)
