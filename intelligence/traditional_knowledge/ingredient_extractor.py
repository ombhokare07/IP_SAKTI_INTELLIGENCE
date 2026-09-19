"""Only ingredient mentions in the supplied input are extracted."""
from multilingual.terminology_normalizer import match_terms
import re

def extract_ingredients(text: str) -> list[dict]:
    mentions=match_terms(text)
    for item in mentions:
        prefix=text[max(0,item['start']-40):item['start']]
        suffix=text[item['end']:item['end']+15]
        item['negated']=bool(re.search(r'\b(?:without|not|no|never)\s*$',prefix,re.I)
                             or re.match(r'\s+(?:नहीं|नाही)(?:\s|[.,;]|$)',suffix))
    return mentions

class IngredientExtractor:
    extract = staticmethod(extract_ingredients)
