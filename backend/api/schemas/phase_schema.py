from datetime import date
from typing import Any, Literal
from pydantic import BaseModel, Field, field_validator, ConfigDict
from intelligence.regulations.jurisdiction_engine import normalize_jurisdiction

class StrictRequest(BaseModel):
    model_config=ConfigDict(extra='forbid',str_strip_whitespace=True)

class TKRequest(StrictRequest):
    title: str = Field(default='',max_length=500)
    description: str = Field(min_length=1,max_length=20000)
    ingredients: list[str] = Field(default_factory=list,max_length=200)
    therapeutic_use: str = Field(default='',max_length=5000)
    process: str = Field(default='',max_length=10000)

class CompareRequest(StrictRequest):
    jurisdictions: list[str] = Field(default=['IN','US','EU','UK'],min_length=1,max_length=4)
    product_category: str = Field(default='herbal_product',min_length=1,max_length=100)
    as_of: date | None = None
    @field_validator('jurisdictions')
    @classmethod
    def countries(cls,v):return list(dict.fromkeys(normalize_jurisdiction(j) for j in v))

class ComplianceRequest(StrictRequest):
    jurisdiction: str = 'IN'
    product_category: str = Field(default='herbal_product',min_length=1,max_length=100)
    document_text: str = Field(default='',max_length=1000000)
    document_id: str | None = Field(default=None,pattern=r'^[a-f0-9]{32}$')
    fields: dict[str,Any] = Field(default_factory=dict,max_length=200)
    as_of: date | None = None
    @field_validator('jurisdiction')
    @classmethod
    def country(cls,v):return normalize_jurisdiction(v)

class AgentRequest(StrictRequest):
    question: str = Field(min_length=1,max_length=20000)
    intent: Literal['ask','patent','ayush','prior_art','traditional_knowledge','international','regulation','compliance','translation','report'] | None = None
    language: Literal['en','hi','mr'] = 'en'
    source_language: Literal['en','hi','mr'] | None = None
    title: str = Field(default='',max_length=500)
    description: str = Field(default='',max_length=20000)
    ingredients: list[str] = Field(default_factory=list,max_length=200)
    process: str = Field(default='',max_length=10000)
    claimed_innovation: str = Field(default='',max_length=10000)
    technical_advantage: str = Field(default='',max_length=10000)
    jurisdiction: str = 'IN'
    jurisdictions: list[str] = Field(default=['IN','US','EU','UK'],min_length=1,max_length=4)
    product_category: str = Field(default='herbal_product',min_length=1,max_length=100)
    fields: dict[str,Any] = Field(default_factory=dict,max_length=200)
    document_text: str = Field(default='',max_length=1000000)
    limit: int = Field(default=10,ge=1,le=100)
    run_prior_art_search: bool = False
    target_language: Literal['en','hi','mr'] | None = None
    @field_validator('jurisdiction')
    @classmethod
    def country(cls,v):return normalize_jurisdiction(v)
    @field_validator('jurisdictions')
    @classmethod
    def countries(cls,v):return list(dict.fromkeys(normalize_jurisdiction(j) for j in v))

class TranslationRequest(StrictRequest):
    text: str = Field(min_length=1,max_length=20000)
    source_language: Literal['en','hi','mr'] | None = None
    target_language: Literal['en','hi','mr'] = 'en'

class DocumentRequest(StrictRequest):
    name: str = Field(min_length=1,max_length=300)
    content_base64: str = Field(min_length=4,max_length=13333340)

class STTRequest(StrictRequest):
    audio_base64: str = Field(min_length=4,max_length=6666670)
    language: Literal['en','hi','mr'] = 'en'
    mime_type: Literal['audio/webm','audio/wav','audio/mpeg','audio/ogg'] = 'audio/webm'
    speak: bool = False

class TTSRequest(StrictRequest):
    text: str = Field(min_length=1,max_length=20000)
    language: Literal['en','hi','mr'] = 'en'

class ReportRequest(StrictRequest):
    title: str = Field(default='IP-SAKTI screening report',min_length=1,max_length=200)
    kind: Literal['patent','prior_art','traditional_knowledge','comparison','compliance','journey','changes','ask']
    input: dict[str,Any] = Field(default_factory=dict,max_length=200)
    assessment_id: str | None = Field(default=None,pattern=r'^[a-f0-9]{32}$')

class ScreeningResponse(BaseModel):
    model_config=ConfigDict(extra='allow')
    status: str
    mode: str

class AgentResponse(ScreeningResponse):
    question: str
    answer: str
    results: dict[str,Any]
    citations: list[dict[str,Any]]
    trust: dict[str,Any]
