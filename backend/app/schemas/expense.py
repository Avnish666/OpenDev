from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ExpenseCreate(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    category: str = Field(min_length=1, max_length=100)
    amount_cents: int = Field(gt=0, le=9223372036854775807, strict=True)
    currency: Literal['USD'] = 'USD'
    vendor: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=10000)
    expense_date: date


class ExpensePatch(ExpenseCreate):
    category: str | None = Field(default=None, min_length=1, max_length=100)
    amount_cents: int | None = Field(default=None, gt=0, le=9223372036854775807, strict=True)
    currency: Literal['USD'] | None = None
    vendor: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, min_length=1, max_length=10000)
    expense_date: date | None = None

    @model_validator(mode='after')
    def no_null_fields(self):
        if any(getattr(self, key) is None for key in self.model_fields_set):
            raise ValueError('Expense fields cannot be null')
        return self


class ExpenseResponse(ExpenseCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    project_id: int
    submitted_by_user_id: int
    evidence_status: Literal['unverified']
    publication_status: Literal['draft', 'published']
    created_at: datetime
    updated_at: datetime


class CategorySummary(BaseModel):
    category: str
    allocated_cents: int
    reported_spending_cents: int
    independently_verified_spending_cents: int
    budget_remaining_cents: int
    overspend_cents: int


class FinancialSummary(BaseModel):
    project_id: int
    currency: str
    completed_funding_cents: int
    excluded_refunded_or_reversed_cents: int
    excluded_other_status_cents: int
    excluded_currency_mismatch_count: int
    reported_spending_cents: int
    independently_verified_spending_cents: int
    allocated_budget_cents: int
    budget_remaining_cents: int
    funding_less_reported_spending_cents: int
    expense_count: int
    categories: list[CategorySummary]
    spending_basis: Literal['published_maintainer_reports'] = 'published_maintainer_reports'
    refund_policy: Literal['exclude_entire_refunded_or_reversed_contribution'] = 'exclude_entire_refunded_or_reversed_contribution'
    notice: str = 'Reported expenses are unverified claims, not proof of fund transfers. Funding is recorded PayPal Sandbox capture data, not a bank balance.'
