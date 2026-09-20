from rag.citations.citation_generator import safe_display_identifier


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
                public={k:v for k,v in c.items() if k!='path'}
                if public.get('source'):
                    public['source']=safe_display_identifier(public['source'])
                locator=c.get('locator') or c.get('source') or (safe_display_identifier(c.get('path')) if c.get('path') else None)
                accepted.append({**public,'id':str(c.get('id') or c.get('citation_id') or len(accepted)+1),
                    'title':c.get('title') or safe_display_identifier(c.get('source')) or 'Retrieved evidence','excerpt':excerpt,
                    'locator':safe_display_identifier(locator),
                    'mode':c.get('mode') or result.get('mode') or 'local','agent':name})
        return {'citations':accepted,'rejected':rejected}
