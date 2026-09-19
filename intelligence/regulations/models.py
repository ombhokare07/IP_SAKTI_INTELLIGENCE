from datetime import date
from typing import Literal
from pydantic import BaseModel, Field, model_validator, field_validator
from intelligence.contracts import Evidence, Mode
from intelligence.regulations.jurisdiction_engine import normalize_jurisdiction

class Requirement(BaseModel):
    id: str = Field(min_length=1,max_length=120)
    field: str = Field(pattern=r'^[a-z][a-z0-9_]{0,79}$')
    label: str = Field(min_length=1,max_length=500)
    description: str = Field(min_length=1,max_length=5000)
    source_excerpt: str = Field(min_length=1,max_length=10000)
    mandatory: bool = True
    operator: Literal['present','equals','minimum'] = 'present'
    expected: str | float | bool | None = None
    @model_validator(mode='after')
    def check_operator(self):
        if self.operator!='present' and self.expected is None:raise ValueError('An expected value is required.')
        if self.operator=='minimum':
            import math
            try:value=float(self.expected)
            except (ValueError,TypeError):raise ValueError('Minimum requires a numeric threshold.')
            if not math.isfinite(value):raise ValueError('Minimum requires a finite threshold.')
        return self

class RegulationVersion(BaseModel):
    regulation_id: str = Field(min_length=1,max_length=120)
    version: str = Field(min_length=1,max_length=120)
    jurisdiction: str
    product_category: str = Field(min_length=1,max_length=100)
    title: str = Field(min_length=1,max_length=1000)
    effective_from: date
    effective_to: date | None = None
    published_at: date
    mode: Mode = 'local'
    evidence: Evidence
    requirements: list[Requirement] = Field(default_factory=list,max_length=200)
    @field_validator('jurisdiction')
    @classmethod
    def jurisdiction_code(cls,value):return normalize_jurisdiction(value)
    @model_validator(mode='after')
    def validate_evidence(self):
        if self.mode=='unconfigured':raise ValueError('A version must have provenance.')
        if self.effective_to and self.effective_to<self.effective_from:raise ValueError('Invalid effective date interval.')
        if len({r.id for r in self.requirements})!=len(self.requirements):raise ValueError('Duplicate requirement IDs.')
        if any(r.source_excerpt not in self.evidence.excerpt for r in self.requirements):
            raise ValueError('Every requirement excerpt must occur verbatim in the supplied source text.')
        if not (self.evidence.source_url or self.evidence.locator):raise ValueError('Source location is required.')
        if self.evidence.mode!=self.mode:raise ValueError('Evidence and regulation modes must match.')
        return self
