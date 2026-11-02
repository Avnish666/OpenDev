from datetime import datetime
from pydantic import BaseModel
from app.schemas.credibility import PublicIdentity, DeliveryRow
from app.schemas.github_progress import ActivityResponse, MilestoneResponse
from app.schemas.roadmap import HistoryResponse


class Counts(BaseModel):
    total: int
    planned: int
    in_progress: int
    submitted_for_review: int
    delivered: int
    cancelled: int
    overdue_unfinished: int
    reopened: int
    on_time: int
    late: int
    unknown_delivery_timing: int


class OwnerSummary(BaseModel):
    identity: PublicIdentity
    public_projects: int
    delivery: Counts
    profile_href: str
    scope: str


class Change(HistoryResponse):
    milestone_id: int
    title: str


class Finance(BaseModel):
    currency: str
    gross_completed_funding_cents: int
    refund_excluded_cents: int
    reversal_excluded_cents: int
    net_recorded_funding_cents: int
    published_reported_spending_cents: int
    funding_minus_reported_expenditure_cents: int
    expenses_with_documents_count: int
    expenses_with_documents_cents: int
    published_expense_count: int
    public_unresolved_discrepancy_count: int
    notes: list[str]


class Attempt(BaseModel):
    status: str
    started_at: datetime
    completed_at: datetime | None
    error_code: str | None


class PublicSync(BaseModel):
    latest: Attempt | None
    last_successful_sync_at: datetime | None
    stale: bool


class ProgressSummary(BaseModel):
    project_id: int
    github_repository_id: int
    calculated_at: datetime
    roadmap_updated_at: datetime | None
    counts: Counts
    linked_issues: int | None
    linked_merged_pull_requests: int | None
    linked_evidence_stale: bool | None
    github_available: bool
    sync: PublicSync
    snapshot_age_seconds: int | None
    activity: ActivityResponse | None
    github_milestones: list[MilestoneResponse]
    delivery_history_preview: list[DeliveryRow]
    recent_changes: list[Change]
    owner: OwnerSummary
    financial: Finance
    links: dict[str,str]
    limitations: list[str]
