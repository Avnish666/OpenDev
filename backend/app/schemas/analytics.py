"""Bounded public analytics projections; no private analytics mode is exposed."""
from datetime import date, datetime
from typing import Literal
from pydantic import BaseModel
from app.schemas.accountability import AccountabilitySnapshot, BudgetVariance
from app.schemas.credibility import DeliveryRow, Indicator, FinancialProject
from app.schemas.progress import Counts, PublicSync
from app.schemas.github_progress import CommitResponse, IssueResponse, PullResponse, MilestoneResponse

class ExpenseRow(BaseModel):
    id: int
    category: str
    amount_cents: int
    currency: str
    expense_date: date
    approved_public_support: bool
    public_category_finding_count: int

class ExpenseGroup(BaseModel):
    key: str
    expense_count: int
    amount_cents: int

class ExpenseAnalysis(BaseModel):
    categories: list[ExpenseGroup]
    months: list[ExpenseGroup]
    expense_count: int
    reported_spending_cents: int
    date_basis: Literal['maintainer_reported_expense_date'] = 'maintainer_reported_expense_date'

class ExpenseFilters(BaseModel):
    category: str = ''
    evidence: Literal['all','supported','unsupported'] = 'all'
    date_from: date | None = None
    date_to: date | None = None
    sort: Literal['date_desc','date_asc'] = 'date_desc'

class FundingTrend(BaseModel):
    available: Literal[False] = False
    reason: str = 'Capture timestamps and dated exact refund/reversal amounts are not retained. Contribution creation time is not capture time; no reliable historic funding series can be shown.'

class DevelopmentMilestone(DeliveryRow):
    overdue: bool
    deadline_shift_days: int | None
    delivery_delay_days: int | None

class GitHubDataset(BaseModel):
    available: bool
    repository_name: str | None
    counts: dict[str,int] | None
    sync: PublicSync
    observed_at: datetime | None
    snapshot_age_seconds: int | None
    issues: list[IssueResponse]
    pull_requests: list[PullResponse]
    milestones: list[MilestoneResponse]
    recent_commits: list[CommitResponse]
    exhaustive: Literal[False] = False
    limitations: list[str]

class DevelopmentDataset(BaseModel):
    counts: Counts
    milestones: list[DevelopmentMilestone]
    total: int
    limit: int
    offset: int
    github: GitHubDataset
    github_counts: dict[str,int] | None
    last_successful_sync_at: datetime | None
    github_stale: bool

class MaintainerDataset(BaseModel):
    project_rewards: list[Indicator]
    owner_id: int
    participation: dict[str,int]
    delivery: list[Indicator]
    rewards: list[Indicator]
    financial: list[FinancialProject]
    scope: str
    attribution: str

class AnalyticsOverview(BaseModel):
    schema_version: Literal['1'] = '1'
    project_id: int
    currency: str
    as_of: datetime
    visibility: Literal['public_active_project'] = 'public_active_project'
    funding_goal_cents: int
    financial: AccountabilitySnapshot
    budget: list[BudgetVariance]
    expenses: list[ExpenseRow]
    expense_analysis: ExpenseAnalysis
    expense_filters: ExpenseFilters
    public_unresolved_finding_count: int
    funding_trend: FundingTrend
    expense_total: int
    expense_limit: int
    expense_offset: int
    development: DevelopmentDataset
    maintainer: MaintainerDataset
    limitations: list[str]
