"""Preserve uploaded document bytes with verifiable identifiers and actual pages."""
import hashlib
from pathlib import Path
from uuid import uuid4
from intelligence.contracts import now_iso

class DocumentService:
    def __init__(self,database,directory):
        self.db,self.directory=database,Path(directory)
        self.directory.mkdir(parents=True,exist_ok=True)
    def add(self,name: str,content: bytes):
        name=Path(name.replace('\\','/')).name
        extension=Path(name).suffix.lower()
        if extension not in {'.pdf','.txt','.md'} or not 0<len(content)<=10_000_000:
            raise ValueError('Upload a PDF, TXT or Markdown file of 1 byte to 10 MB.')
        if extension=='.pdf':
            import fitz
            try:
                with fitz.open(stream=content,filetype='pdf') as doc:
                    if doc.needs_pass:raise ValueError('Encrypted PDFs require an unlocked copy.')
                    if len(doc)>500:raise ValueError('PDF exceeds 500 pages.')
                    pages=[{'page':index+1,'text':p.get_text('text')} for index,p in enumerate(doc)]
            except Exception as e:raise ValueError('PDF could not be read. Supply an unlocked, readable PDF.') from e
        else:
            try:text=content.decode('utf-8-sig')
            except UnicodeDecodeError as e:raise ValueError('Text documents must use UTF-8.') from e
            pages=[{'page':None,'text':text}]
        if sum(len(p['text']) for p in pages)>1_000_000:raise ValueError('Extracted text exceeds 1 million characters.')
        identifier=uuid4().hex
        path=self.directory/f'{identifier}{extension}'
        path.write_bytes(content)
        record={'id':identifier,'name':name,'extension':extension,'size_bytes':len(content),'sha256':hashlib.sha256(content).hexdigest(),
                'created_at':now_iso(),'pages':pages,'page_count':len(pages) if extension=='.pdf' else None,
                'status':'stored' if any(p['text'].strip() for p in pages) else 'no_extractable_text',
                'source_verified':False,'rag_indexed':False,'mode':'local'}
        self.db.put('document',identifier,record)
        return record
    def list(self):
        return [{k:v for k,v in d.items() if k!='pages'} for d in self.db.list('document')]
    def get(self,identifier):return self.db.get('document',identifier)
    def text(self,identifier):
        record=self.get(identifier)
        if not record:raise KeyError(identifier)
        return '\n'.join(p['text'] for p in record['pages'])
    def file_path(self,identifier):
        record=self.get(identifier)
        if not record:raise KeyError(identifier)
        path=self.directory/f'{record["id"]}{record["extension"]}'
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=record['sha256']:
            raise ValueError('Stored document bytes are missing or changed.')
        return path
