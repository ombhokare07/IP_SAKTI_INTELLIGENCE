"""Explicit offline/local/authorized-gateway TK corpus providers. No TKDL adapter."""
import json
from pathlib import Path
from typing import Protocol
from pydantic import BaseModel, Field, ValidationError
from intelligence.contracts import Evidence
from services.provider_gateway import ProviderUnavailable

class TKRecord(BaseModel):
    id: str = Field(min_length=1)
    evidence: Evidence

class TKProvider(Protocol):
    mode: str
    authorized: bool
    def search(self,query: str) -> list[TKRecord]: ...

class LocalTKProvider:
    mode='local'
    def __init__(self,path: Path,*,authorized=False,mock=False):
        self.path=Path(path)
        self.mode='mock' if mock else 'local'
        self.authorized=authorized and not mock
    def search(self,query):
        try:
            payload=json.loads(self.path.read_text(encoding='utf-8'))
            if not isinstance(payload,dict) or not isinstance(payload.get('records'),list): raise ValueError
            if payload.get('synthetic') and self.mode!='mock': raise ValueError
            records=[TKRecord.model_validate(r) for r in payload['records']]
            if len({r.id for r in records})!=len(records):raise ValueError
            for r in records:r.evidence.mode=self.mode
            return records
        except (OSError,ValueError,ValidationError) as e:
            raise ProviderUnavailable('tk_corpus_invalid') from e

class GatewayTKProvider:
    mode='live'
    def __init__(self,gateway,*,authorized=False):self.gateway,self.authorized=gateway,authorized
    def search(self,query):
        if not self.authorized:raise ProviderUnavailable('tk_search_not_authorized')
        try:
            result=self.gateway.call({'operation':'search_tk','query':query,'limit':100})
            if not isinstance(result.get('records'),list):raise ValueError
            if result.get('mode') != 'live':raise ValueError
            records=[TKRecord.model_validate(r) for r in result['records'][:100]]
            if any(r.evidence.mode=='mock' for r in records):raise ValueError
            for r in records:r.evidence.mode='live'
            return records
        except (ValueError,ValidationError) as e:raise ProviderUnavailable('tk_provider_malformed_response') from e
