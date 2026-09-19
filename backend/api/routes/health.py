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
          ('authorization_required' if not cfg.tk_search_authorized else gateway_status(cfg.tk_provider,cfg.tk_api_url,cfg.tk_api_key))
          if cfg.tk_provider=='http_json' else s.tk.provider.mode if s.tk.provider else 'unconfigured'),
      'regulations':(gateway_status(cfg.regulation_provider,cfg.regulation_api_url,cfg.regulation_api_key)
          if cfg.regulation_provider=='http_json' else s.regulations.mode),
      'translation':gateway_status(cfg.translation_provider,cfg.translation_api_url,cfg.translation_api_key),
      'speech_to_text':gateway_status(cfg.stt_provider,cfg.stt_api_url,cfg.stt_api_key),
      'text_to_speech':gateway_status(cfg.tts_provider,cfg.tts_api_url,cfg.tts_api_key),
    }
    return {'status':'running','version':'1.0.0','providers':providers,'tkdl_access':False,
            'rag':rag_details,
            'authentication_required':cfg.api_auth_required or cfg.app_env.casefold()=='production',
            'regulation_sync':s.regulations.sync_status,'documents':len(s.documents.list()),'reports':len(s.reports.list()),
            'configuration_errors':s.configuration_errors,
            'limitations':['Configured providers are not verified until a successful request. Offline fixtures never represent live search.']}
@router.get('/alerts')
def alerts(request:Request):return services(request).alerts.list()
@router.post('/alerts/{identifier}/acknowledge')
def acknowledge(identifier:str,request:Request):
    try:return services(request).alerts.acknowledge(identifier)
    except KeyError:raise HTTPException(404,'Alert not found.')
