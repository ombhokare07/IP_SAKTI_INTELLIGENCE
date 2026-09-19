from difflib import unified_diff

def diff_regulations(old: dict,new: dict) -> dict:
    if any(old[k]!=new[k] for k in ('regulation_id','jurisdiction','product_category','mode')):
        raise ValueError('Diff requires versions of the same regulation, category, jurisdiction and provenance mode.')
    before={r['id']:r for r in old['requirements']};after={r['id']:r for r in new['requirements']}
    added=[after[k] for k in sorted(after.keys()-before.keys())]
    removed=[before[k] for k in sorted(before.keys()-after.keys())]
    changed=[{'before':before[k],'after':after[k]} for k in sorted(before.keys()&after.keys()) if before[k]!=after[k]]
    metadata={k:{'before':old.get(k),'after':new.get(k)} for k in ('effective_from','effective_to','published_at','title') if old.get(k)!=new.get(k)}
    return {'regulation_id':new['regulation_id'],'jurisdiction':new['jurisdiction'],'mode':new['mode'],
            'from_version':old['version'],'to_version':new['version'],'effective_from':new['effective_from'],
            'added':added,'removed':removed,'changed':changed,'metadata_changes':metadata,
            'text_diff':'\n'.join(unified_diff(old['evidence']['excerpt'].splitlines(),new['evidence']['excerpt'].splitlines(),fromfile=old['version'],tofile=new['version'],lineterm='')),
            'citations':[old['evidence'],new['evidence']],
            'limitations':['This compares stored snapshots; it does not establish legal effect or regulatory completeness.']}

class RegulationDiff:
    compare=staticmethod(diff_regulations)
