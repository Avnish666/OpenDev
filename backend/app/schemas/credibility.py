from datetime import date, datetime
from typing import Literal
from pydantic import BaseModel


class Indicator(BaseModel):
    key: str
    label: str
    numerator: int | None
    denominator: int | None
    sample_size: int
    state: Literal['recorded','insufficient_history','unavailable']
    formula: str
    calculated_at: datetime
    last_updated_at: datetime | None
    limitations: list[str]
    source_links: list[str]


class PublicIdentity(BaseModel):
    user_id: int
    github_id: int | None
    username: str
    avatar_url: str | None
    github_profile_url: str | None


class PublicProject(BaseModel):
    id: int
    title: str
    status: Literal['active']
    role: Literal['owner','maintainer','collaborator']
    project_href: str


class ProjectPage(BaseModel):
    items: list[PublicProject]
    total: int
    limit: int
    offset: int
    calculated_at: datetime


class DeliveryRow(BaseModel):
    milestone_id: int
    project_id: int
    title: str
    status: str
    original_deadline: date | None
    current_deadline: date
    actual_completion_date: date | None
    timing: Literal['on_time','late','not_currently_delivered','unknown']
    ever_asserted_delivered: bool
    reopened_after_delivery: bool
    evidence_links_at_delivery: int | None
    independently_reviewed: Literal[False] = False
    updated_at: datetime
    project_href: str
    history_path: str


class DeliveryPage(BaseModel):
    items: list[DeliveryRow]
    total: int
    limit: int
    offset: int
    calculated_at: datetime


class FinancialProject(BaseModel):
    project_id: int
    reporting_available: bool
    currency: str
    published_reported_spending_cents: int
    document_supported_expense_cents: int
    last_reporting_activity: datetime | None
    metrics: list[Indicator]
    notes: list[str]


class GitHubProject(BaseModel):
    project_id: int
    repository_name: str | None
    last_successful_sync_at: datetime | None
    stale: bool
    metrics: list[Indicator]


class CredibilityProfile(BaseModel):
    identity: PublicIdentity
    calculated_at: datetime
    attribution: str
    scope: str
    participation: dict[str,int]
    delivery: list[Indicator]
    rewards: list[Indicator]
    financial: list[FinancialProject]
    github: list[GitHubProject]
    limitations: list[str]
