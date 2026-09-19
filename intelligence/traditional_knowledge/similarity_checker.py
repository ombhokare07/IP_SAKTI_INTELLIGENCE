"""Transparent lexical feature overlap, not a novelty or TK clearance judgment."""
from intelligence.traditional_knowledge.ingredient_extractor import extract_ingredients
from intelligence.traditional_knowledge.therapeutic_use_extractor import extract_therapeutic_uses
from intelligence.traditional_knowledge.process_extractor import extract_processes

def extract_features(text):
    return {'ingredients':extract_ingredients(text),'therapeutic_uses':extract_therapeutic_uses(text),'processes':extract_processes(text)}

def compare_features(left: dict,right: dict):
    details={}
    for category in ('ingredients','therapeutic_uses','processes'):
        a={r['canonical'] for r in left[category] if not r.get('negated')}
        b={r['canonical'] for r in right[category] if not r.get('negated')}
        details[category]={'matched':sorted(a&b),'input_only':sorted(a-b),
                           'jaccard':len(a&b)/len(a|b) if a|b else None}
    weights={'ingredients':0.45,'therapeutic_uses':0.35,'processes':0.20}
    present=[k for k,v in details.items() if v['jaccard'] is not None]
    score=round(100*sum(weights[k]*details[k]['jaccard'] for k in present)/sum(weights[k] for k in present)) if present else 0
    return {'score':score,'method':'dictionary_feature_jaccard','features':details,
            'limitations':['Dictionary overlap misses synonyms, context, negation and unlisted knowledge. A match is a review lead only.']}

class SimilarityChecker:
    compare=staticmethod(compare_features)
