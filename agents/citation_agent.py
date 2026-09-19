class CitationAgent:
    name='citation'
    def run(self,results):
        accepted=[];rejected=[];seen=set()
        for name,result in results.items():
            for index,c in enumerate(result.get('citations') or []):
                source=c.get('source_url') or c.get('locator') or c.get('path') or c.get('source')
                excerpt=c.get('excerpt') or c.get('text')
                if not source or not excerpt:
                    rejected.append({'agent':name,'index':index,'reason':'Missing source locator or excerpt.'});continue
                key=(source,c.get('page'),excerpt)
                if key in seen:continue
                seen.add(key)
                accepted.append({**c,'id':str(c.get('id') or c.get('citation_id') or len(accepted)+1),
                    'title':c.get('title') or c.get('source') or 'Retrieved evidence','excerpt':excerpt,
                    'locator':c.get('locator') or c.get('path') or c.get('source'),
                    'mode':c.get('mode') or result.get('mode') or 'local','agent':name})
        return {'citations':accepted,'rejected':rejected}
