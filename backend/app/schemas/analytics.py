"""Bounded public analytics projections; no private analytics mode is exposed."""
from datetime import date, datetime
from typing import Literal
from pydantic import BaseModel
from app.schemas.accountability import AccountabilitySnapshot, BudgetVariance
from app.schemas.credibility import DeliveryRow, Indicator, FinancialProject
from app.schemas.progress import Counts

class ExpenseRow(BaseModel):
    id: int
    category: str
    amount_cents: int
    currency: str
    expense_date: date
    approved_public_support: bool
    public_category_finding_count: int

class DevelopmentDataset(BaseModel):
    counts: Counts
    milestones: list[DeliveryRow]
    total: int
    limit: int
    offset: int
    github_counts: dict[str,int] | None
    last_successful_sync_at: datetime | None
    github_stale: bool

class MaintainerDataset(BaseModel):
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
    expense_total: int
    expense_limit: int
    expense_offset: int
    development: DevelopmentDataset
    maintainer: MaintainerDataset
    limitations: list[str]
