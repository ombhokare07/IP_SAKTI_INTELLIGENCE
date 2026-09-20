from copy import deepcopy
from fastapi import APIRouter,Request,HTTPException
from backend.api.routes.common import services
router=APIRouter(tags=['workspace'])
@router.get('/status')
def status(request:Request):
    s=services(request);cfg=s.settings
    prior=getattr(request.app.state,'prior_art_engine',None)
    rag_details=getattr(request.app.state,'rag_status',None)
    def gateway_status(provider,url,key):return 'configured_not_verified' if provider=='http_json' and url and key.get_secret_value() else 'unconfigured'
    providers={
      'rag':'initialized' if getattr(request.app.state,'rag_pipeline',None) else 'unconfigured',
      'prior_art':('mock' if getattr(prior.provider,'is_test_fixture',False) else 'configured_not_verified') if prior else 'unconfigured',
      'traditional_knowledge':(
          'unconfigured' if not s.tk.provider else
          'mock' if s.tk.provider.mode=='mock' else
          'authorization_required' if not s.tk.provider.authorized else
          gateway_status(cfg.tk_provider,cfg.tk_api_url,cfg.tk_api_key) if cfg.tk_provider=='http_json' else
          s.tk.provider.mode),
      'regulations':(gateway_status(cfg.regulation_provider,cfg.regulation_api_url,cfg.regulation_api_key)
          if cfg.regulation_provider=='http_json' else s.regulations.mode),
      'translation':gateway_status(cfg.translation_provider,cfg.translation_api_url,cfg.translation_api_key),
      'speech_to_text':gateway_status(cfg.stt_provider,cfg.stt_api_url,cfg.stt_api_key),
      'text_to_speech':gateway_status(cfg.tts_provider,cfg.tts_api_url,cfg.tts_api_key),
    }
    rag=deepcopy(rag_details or {})
    pipeline_status=(rag.get('pipeline') or {}).get('status')
    vector_status=(rag.get('vector_store') or {}).get('status')
    document_status=(rag.get('documents') or {}).get('status')
    gemini_status=(rag.get('gemini') or {}).get('status','not_configured')
    embedding_status=(rag.get('embedding_model') or {}).get('status','unavailable')
    if pipeline_status=='ready' and document_status=='indexed':
        overall_rag='ready'
    elif any(value in {'available','initialized','configured','ready','indexed'} for value in (embedding_status,vector_status,gemini_status,document_status)):
        overall_rag='degraded'
    else:
        overall_rag='unavailable'
    rag['status']=overall_rag
    rag['gemini_readiness']={'status':'ready' if pipeline_status=='ready' else 'configured' if gemini_status=='configured' else 'unconfigured'}
    rag['embeddings']={'status':'ready' if embedding_status=='available' else 'unavailable','model':(rag.get('embedding_model') or {}).get('model')}
    rag['vector_store_readiness']={'status':'ready' if vector_status=='initialized' else 'unavailable'}
    rag['knowledge_base']={'status':'indexed' if document_status=='indexed' else 'empty' if document_status=='not_indexed' else 'unavailable',
                           'indexed_chunks':(rag.get('documents') or {}).get('indexed_chunks',0)}
    rag['grounded_chat']={'status':'available' if pipeline_status=='ready' and document_status=='indexed' else 'unavailable'}
    auth_required=cfg.api_auth_required or cfg.app_env.casefold()=='production'
    provider_status={
      'prior_art':{'status':'configured' if prior else 'unconfigured','provider':cfg.prior_art_provider or None},
      'traditional_knowledge':{'status':'configured' if s.tk.provider else 'unconfigured','provider':cfg.tk_provider or None,
                               'authorized':bool(s.tk.provider and s.tk.provider.authorized),'tkdl_connected':False},
      'regulations':{'status':'configured' if s.regulations.provider else 'unconfigured','provider':cfg.regulation_provider or None},
      'translation':{'status':'configured' if cfg.translation_provider=='http_json' and cfg.translation_api_url and cfg.translation_api_key.get_secret_value() else 'unconfigured'},
      'speech_to_text':{'status':'configured' if cfg.stt_provider=='http_json' and cfg.stt_api_url and cfg.stt_api_key.get_secret_value() else 'unconfigured'},
      'text_to_speech':{'status':'configured' if cfg.tts_provider=='http_json' and cfg.tts_api_url and cfg.tts_api_key.get_secret_value() else 'unconfigured'},
    }
    return {'status':'running','version':'1.0.0','providers':providers,'tkdl_access':False,
            'provider_status':provider_status,'rag':rag,
            'authentication_required':auth_required,
            'authentication':{'status':'enabled' if auth_required else 'disabled','token_required':auth_required},
            'regulation_sync':s.regulations.sync_status,'documents':len(s.documents.list()),'reports':len(s.reports.list()),
            'configuration_errors':s.configuration_errors,
            'limitations':['Configured providers are not verified until a successful request. Offline fixtures never represent live search.']}
@router.get('/alerts')
def alerts(request:Request):return services(request).alerts.list()
@router.post('/alerts/{identifier}/acknowledge')
def acknowledge(identifier:str,request:Request):
    try:return services(request).alerts.acknowledge(identifier)
    except KeyError:raise HTTPException(404,'Alert not found.')
