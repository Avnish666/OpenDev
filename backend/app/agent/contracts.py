from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, JsonValue


class AgentQuestion(BaseModel):
    model_config=ConfigDict(extra='forbid',str_strip_whitespace=True)
    project_id: int = Field(gt=0,le=9223372036854775807,strict=True)
    question: str = Field(min_length=3,max_length=1000)
    mode: Literal['deterministic','llm','auto'] | None = None


class Citation(BaseModel):
    reference: str
    source_id: str
    api_path: str
    method: Literal['GET','POST']='GET'
    request_body: dict | None = None
    projection_sha256: str
    retrieved_at: datetime


class AgentEvidence(BaseModel):
    source_type: str
    source_id: str
    project_id: int | None
    claim: str
    value: JsonValue
    observed_at: datetime
    last_updated_at: datetime | None
    visibility: Literal['public_active_projects']='public_active_projects'
    freshness: Literal['current_database_snapshot','stale','unknown']
    citation: Citation
    limitations: list[str]


class AgentAnswer(BaseModel):
    answer: str
    citations: list[Citation]=Field(default_factory=list)
    evidence_used: list[AgentEvidence]=Field(default_factory=list)
    limitations: list[str]
    confidence: Literal['deterministic_records','limited_evidence','not_applicable']
    answer_status: Literal['answered','insufficient_evidence','unsupported_question','unavailable_source','provider_unavailable']
    execution_mode: Literal['deterministic','llm'] = 'deterministic'
    source_freshness: dict[str,str] = Field(default_factory=dict)
    diagnostics: dict = Field(default_factory=dict)


class ToolCall(BaseModel):
    model_config=ConfigDict(extra='forbid')
    name: Literal['get_project_overview','get_project_finances','get_project_expenses','get_project_roadmap','get_github_activity','get_maintainer_history','get_reward_fulfillment']
    identifier: int = Field(gt=0,le=9223372036854775807,strict=True)
    offset: int = Field(default=0,ge=0,le=10000,strict=True)
