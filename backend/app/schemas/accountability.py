from datetime import datetime
from typing import Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, model_validator

EvidenceState = Literal['self_reported','document_attached','extraction_consistent','discrepancy_detected','human_reviewed','independently_payment_matched']


class ReviewCreate(BaseModel):
    model_config = ConfigDict(extra='forbid',str_strip_whitespace=True)
    request_key: UUID
    action: Literal['explain','accept_field','dispute_field','mark_reviewed','request_retry']
    reason: str = Field(min_length=10,max_length=2000)
    field_name: Literal['total_cents','currency','vendor_name','document_date','invoice_number','subtotal_cents','tax_cents','discount_cents'] | None = None

    @model_validator(mode='after')
    def field_action(self):
        if self.action in ('accept_field','dispute_field') and not self.field_name:
            raise ValueError('Field acceptance/dispute requires a field name')
        if self.action not in ('accept_field','dispute_field') and self.field_name:
            raise ValueError('This action does not accept a field name')
        return self


class ReviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    extraction_id: str
    actor_id: int
    action: str
    field_name: str | None
    finding_reference: str
    finding_snapshot: dict
    reason: str
    created_at: datetime
    outcome: Literal['unresolved','no_longer_detected','awaiting_reconciliation'] = 'unresolved'


class ReviewFinding(BaseModel):
    id: str
    extraction_id: str
    finding_code: str
    severity: Literal['info','warning']
    reported_value: str | int | None
    extracted_value: str | int | None
    explanation: str
    evidence_reference: dict
    review_status: Literal['human_review_required','reviewed','accepted','disputed']
    resolved: Literal[False] = False


class ExpenseVerification(BaseModel):
    expense_id: int
    publication_status: str
    amount_cents: int
    currency: str
    audience: Literal['manager_private','public_evidence_only']
    evidence_states: list[EvidenceState]
    classification: EvidenceState
    approved_public_document_ids: list[str]
    supporting_document_count: int
    independently_payment_matched: Literal[False] = False
    unresolved_discrepancy_count: int | None
    findings: list[ReviewFinding]
    reviews_available: bool
    notice: str = 'Evidence and human opinions are not proof of vendor payment or fraud. Private findings and reviewer notes are not published.'


class BudgetVariance(BaseModel):
    category: str
    allocated_cents: int
    reported_spending_cents: int
    remaining_cents: int
    overspend_cents: int


class Coverage(BaseModel):
    classification: EvidenceState
    expense_count: int
    amount_cents: int


class AccountabilitySnapshot(BaseModel):
    project_id: int
    currency: str
    audience: Literal['manager_private','public_evidence_only']
    gross_completed_funding_cents: int
    refund_excluded_cents: int
    reversal_excluded_cents: int
    exact_refund_total_cents: None = None
    net_recorded_funding_cents: int
    published_reported_spending_cents: int
    funding_minus_reported_expenditure_cents: int
    published_expense_count: int
    expenses_with_documents_count: int
    expenses_with_documents_cents: int
    expenses_without_documents_count: int
    expenses_without_documents_cents: int
    unresolved_expenses_count: int | None
    unresolved_discrepancy_count: int | None
    independently_payment_matched_cents: Literal[0] = 0
    evidence_coverage: list[Coverage]
    budget_variance: list[BudgetVariance]
    calculated_at: datetime
    notes: list[str]


class BudgetVarianceResponse(BaseModel):
    project_id: int
    currency: str
    categories: list[BudgetVariance]
    calculated_at: datetime
