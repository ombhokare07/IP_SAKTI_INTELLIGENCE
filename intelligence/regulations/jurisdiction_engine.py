"""Jurisdiction identifiers only; this table does not contain legal requirements."""
JURISDICTIONS={
 'IN':{'name':'India','languages':['en','hi','mr']},
 'US':{'name':'USA','languages':['en']},
 'EU':{'name':'European Union','languages':['en']},
 'UK':{'name':'United Kingdom','languages':['en']},
}
ALIASES={'india':'IN','in':'IN','usa':'US','us':'US','united states':'US','eu':'EU','european union':'EU','uk':'UK','gb':'UK','united kingdom':'UK'}

def normalize_jurisdiction(value):
    code=ALIASES.get(value.strip().casefold())
    if not code:raise ValueError('Supported jurisdictions: India/IN, USA/US, EU and UK/GB.')
    return code
class JurisdictionEngine:
    normalize=staticmethod(normalize_jurisdiction)
    def list(self):return [{'code':k,**v} for k,v in JURISDICTIONS.items()]
