import re

def extract_mentions(text: str, dictionary: dict[str, list[str]]) -> list[dict]:
    found=[]
    for canonical,terms in dictionary.items():
        for term in sorted(terms,key=len,reverse=True):
            match=re.search(r'(?<![\w\u0900-\u097f])'+re.escape(term)+r'(?![\w\u0900-\u097f])',text,re.I)
            if match:
                prefix=text[max(0,match.start()-35):match.start()]
                negated=bool(re.search(r'\b(?:not|no|without|never)\b[^.;!?]*$',prefix,re.I))
                found.append({'canonical':canonical,'original':match.group(),'start':match.start(),
                              'end':match.end(),'negated':negated,'method':'phrase_dictionary'})
                break
    return sorted(found,key=lambda v:v['start'])
