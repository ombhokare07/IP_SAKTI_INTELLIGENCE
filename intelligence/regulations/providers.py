import json
from pathlib import Path
from typing import Protocol
from intelligence.regulations.models import RegulationVersion
from services.provider_gateway import ProviderUnavailable

class RegulationProvider(Protocol):
    mode: str
    def versions(self) -> list[RegulationVersion]: ...

class LocalRegulationProvider:
    def __init__(self,path,*,mock=False):self.path,self.mode=Path(path),'mock' if mock else 'local'
    def versions(self):
        try:
            data=json.loads(self.path.read_text(encoding='utf-8'))
            if data.get('synthetic') and self.mode!='mock':raise ValueError
            records=[RegulationVersion.model_validate(r) for r in data['versions']]
            if any(r.mode!=self.mode for r in records):raise ValueError
            return records
        except (OSError,ValueError,KeyError,TypeError,AttributeError) as e:raise ProviderUnavailable('regulation_corpus_invalid') from e

class GatewayRegulationProvider:
    mode='live'
    def __init__(self,gateway):self.gateway=gateway
    def versions(self):
        try:
            data=self.gateway.call({'operation':'regulation_versions','jurisdictions':['IN','US','EU','UK']})
            if data.get('mode')!='live' or not isinstance(data.get('versions'),list):raise ValueError
            records=[RegulationVersion.model_validate(r) for r in data['versions']]
            if any(r.mode!='live' for r in records):raise ValueError
            return records
        except (ValueError,KeyError,TypeError) as e:raise ProviderUnavailable('regulation_provider_malformed_response') from e
