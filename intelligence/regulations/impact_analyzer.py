def analyze_impact(diff: dict,fields: dict | None = None) -> dict:
    fields=fields or {}
    affected=sorted({r['field'] for r in diff['added']+diff['removed']} | {c['after']['field'] for c in diff['changed']} | {c['before']['field'] for c in diff['changed']})
    return {'affected_fields':affected,'missing_affected_fields':[f for f in affected if fields.get(f) in (None,'',[])],
            'review_priority':'high' if any(r['mandatory'] for r in diff['added']) or diff['changed'] else 'normal',
            'actions':[f'Review {f.replace("_"," ")} against the changed source requirements.' for f in affected],
            'legal_impact':'undetermined','citations':diff['citations']}
class ImpactAnalyzer:
    analyze=staticmethod(analyze_impact)
