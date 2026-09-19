import base64
import binascii
from fastapi import APIRouter,Request,HTTPException
from fastapi.responses import FileResponse
from backend.api.schemas.phase_schema import DocumentRequest
from backend.api.routes.common import services
router=APIRouter(prefix='/documents',tags=['documents'])
@router.get('')
def list_documents(request:Request):return {'documents':services(request).documents.list()}
@router.post('',status_code=201)
def upload(payload:DocumentRequest,request:Request):
    try:return services(request).documents.add(payload.name,base64.b64decode(payload.content_base64,validate=True))
    except (ValueError,binascii.Error):raise HTTPException(422,'Upload a readable PDF or UTF-8 TXT/MD file up to 10 MB using valid base64.')
@router.get('/{identifier}')
def document(identifier:str,request:Request):
    record=services(request).documents.get(identifier)
    if record is None:raise HTTPException(404,'Document not found.')
    return record
@router.get('/{identifier}/file')
def download(identifier:str,request:Request):
    service=services(request).documents
    try:
        path=service.file_path(identifier)
        return FileResponse(path,filename=service.get(identifier)['name'])
    except KeyError:raise HTTPException(404,'Document not found.')
    except ValueError:raise HTTPException(409,'Stored document is missing or has changed.')
@router.post('/{identifier}/ingest')
def ingest(identifier:str,request:Request):
    service=services(request)
    document=service.documents.get(identifier)
    if not document:raise HTTPException(404,'Document not found.')
    if document['extension']!='.pdf':raise HTTPException(422,'The preserved Phase-1 ingestion pipeline accepts PDFs.')
    try:
        from scripts.ingest_documents import ingest_pdf
        from rag.embeddings.embedding_service import BGEEmbeddingService
        from database.vector.vector_store import ChromaVectorStore
        count=ingest_pdf(service.documents.file_path(identifier),
            BGEEmbeddingService(model_name=service.settings.embedding_model),
            ChromaVectorStore(service.settings.vector_db_path,service.settings.vector_collection),
            chunk_size=service.settings.chunk_size,overlap=service.settings.chunk_overlap)
    except Exception:
        raise HTTPException(503,'Indexing failed or the embedding model is unavailable. The stored document is retained; a partial index write may require retry.')
    document['rag_indexed']=count>0
    document['indexed_chunks']=count
    service.db.put('document',identifier,document)
    return {'status':'indexed' if count else 'no_extractable_text','stored_chunks':count,'document':document}
