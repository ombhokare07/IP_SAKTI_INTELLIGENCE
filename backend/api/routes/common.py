from fastapi import HTTPException,Request
from uuid import uuid4

def remember(request, kind, payload, result):
    service=getattr(request.app.state,'services',None)
    if service is None:return result
    identifier=uuid4().hex
    result={**result,'assessment_id':identifier}
    service.db.put('assessment',identifier,{'kind':kind,'input':payload,'result':result},immutable=True)
    return result

def services(request: Request):
    service=getattr(request.app.state,'services',None)
    if service is None:raise HTTPException(503,'Application services have not started.')
    return service

def compliance_payload(payload,service):
    values=payload.model_dump(mode='json')
    if values.get('document_id'):
        try:values['document_text']=service.documents.text(values['document_id'])
        except KeyError:raise HTTPException(404,'Document not found.')
    return values
