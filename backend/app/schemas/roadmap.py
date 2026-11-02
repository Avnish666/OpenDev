from datetime import date, datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator

State = Literal['planned','in_progress','submitted_for_review','delivered','cancelled']


class Commitment(BaseModel):
    model_config = ConfigDict(extra='forbid',str_strip_whitespace=True)
    title: str = Field(min_length=3,max_length=200)
    description: str = Field(min_length=1,max_length=10000)
    deliverable_description: str = Field(min_length=10,max_length=10000)
    planned_start_date: date
    planned_end_date: date
    display_order: int = Field(default=0,ge=0,le=2147483647,strict=True)

    @model_validator(mode='after')
    def dates(self):
        if self.planned_start_date > self.planned_end_date:raise ValueError('Start date must precede end date')
        return self


class Versioned(BaseModel):
    model_config = ConfigDict(extra='forbid',str_strip_whitespace=True)
    expected_version: int = Field(gt=0,strict=True)
    reason: str = Field(min_length=10,max_length=2000)


class RoadmapPatch(Versioned):
    title: str | None = Field(default=None,min_length=3,max_length=200)
    description: str | None = Field(default=None,min_length=1,max_length=10000)
    deliverable_description: str | None = Field(default=None,min_length=10,max_length=10000)
    planned_start_date: date | None = None
    planned_end_date: date | None = None
    display_order: int | None = Field(default=None,ge=0,le=2147483647,strict=True)

    @model_validator(mode='after')
    def no_null(self):
        if any(getattr(self,k) is None for k in self.model_fields_set):raise ValueError('Explicit null not supported')
        return self


class StatusChange(Versioned):
    status: State


class EvidenceCreate(Versioned):
    evidence_type: Literal['issue','pull_request','github_milestone','commit']
    canonical_id: str = Field(min_length=1,max_length=40)

    @model_validator(mode='after')
    def canonical(self):
        value=self.canonical_id
        if self.evidence_type=='commit':
            if len(value)!=40 or any(c not in '0123456789abcdef' for c in value):raise ValueError('Full lowercase commit SHA required')
        elif not value.isascii() or not value.isdecimal() or str(int(value))!=value or not 0<int(value)<=9223372036854775807:
            raise ValueError('Canonical positive GitHub numeric ID required, not number or URL')
        return self


class EvidenceResponse(BaseModel):
    id: str
    evidence_type: str
    canonical_id: str | None
    url: str | None
    state: str | None
    merged: bool | None
    snapshot_available: bool
    stale: bool
    last_observed_at: datetime | None


class MilestoneResponse(Commitment):
    id: int
    project_id: int
    status: State
    actual_completion_date: date | None
    version: int
    created_by: int
    created_at: datetime
    updated_at: datetime
    evidence: list[EvidenceResponse]
    development_signals: dict[str,int]
    notice: str = 'Delivery is a maintainer-reported assertion. GitHub activity does not certify fulfillment.'


class RoadmapPage(BaseModel):
    items: list[MilestoneResponse]
    total: int
    limit: int
    offset: int


class HistoryResponse(BaseModel):
    id: str
    version: int
    previous_status: str | None
    new_status: str
    actor_id: int
    action: str
    reason: str
    before: dict
    after: dict
    created_at: datetime
