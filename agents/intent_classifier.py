"""Auditable keyword routing. Explicit UI intent takes precedence over heuristics."""
import re
RULES={
 'prior_art':('prior art','prior-art','patent search','पूर्व कला'),
 'traditional_knowledge':('traditional knowledge','tk risk','tkdl','पारंपरिक ज्ञान'),
 'patent':('patentability','patent','novelty','पेटेंट','पेटंट'),
 'international':('compare','comparison','international','usa','european','uk','तुलना'),
 'compliance':('compliance','document check','missing fields','अनुपालन'),
 'regulation':('regulation','regulatory','requirements','नियम'),
 'ayush':('ayush','ayurveda','ayurvedic','आयुर्वेद'),
 'translation':('translate','translation','अनुवाद','भाषांतर'),
 'report':('report','अहवाल','रिपोर्ट'),
}
class IntentClassifier:
    def classify(self,text,explicit=None):
        if explicit:
            if explicit not in (*RULES,'ask'):raise ValueError('Unsupported intent.')
            return {'primary':explicit,'intents':[explicit],'method':'explicit','matched_terms':{}}
        matches={k:[word for word in words if re.search(r'(?<!\w)'+re.escape(word)+r'(?!\w)',text,re.I)] for k,words in RULES.items()}
        matches={k:v for k,v in matches.items() if v}
        if 'prior_art' in matches:matches.pop('patent',None)
        if 'international' in matches:matches.pop('regulation',None)
        # Report/translation without explicit intent never cause side effects.
        matches.pop('report',None);matches.pop('translation',None)
        intents=list(matches)[:4] or ['ask']
        return {'primary':intents[0],'intents':intents,'method':'deterministic_keywords','matched_terms':matches,
                'limitations':['Keyword routing may miss implicit or mixed-language intent. Select a task explicitly when needed.']}
