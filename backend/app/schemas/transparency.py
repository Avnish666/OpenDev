"""Explicit public allowlists; never serialize source documents or extractions."""
from datetime import date, datetime
from typing import Literal
from pydantic import BaseModel
from app.schemas.accountability import AccountabilitySnapshot


class PublicFinding(BaseModel):
    category: str
    finding_code: Literal['CATEGORY_BUDGET_OVERRUN'] = 'CATEGORY_BUDGET_OVERRUN'
    severity: Literal['warning'] = 'warning'
    explanation: str = 'Published reported spending exceeds the allocated category budget.'
    unresolved: Literal[True] = True
    scope: Literal['published_category_totals'] = 'published_category_totals'


class PublicEvidence(BaseModel):
    id: str
    detected_mime_type: str
    status: Literal['approved_redacted'] = 'approved_redacted'


class LedgerEntry(BaseModel):
    id: int
    project_id: int
    currency: str
    category: str
    vendor: str
    description: str
    amount_cents: int
    expense_date: date
    updated_at: datetime
    public_evidence_status: Literal['self_reported', 'approved_redacted_document_attached']
    evidence: list[PublicEvidence]
    findings: list[PublicFinding]
    independently_payment_matched: Literal[False] = False


class PublicTransparency(BaseModel):
    financial_summary: AccountabilitySnapshot
    public_findings: list[PublicFinding]
    public_unresolved_discrepancy_count: int
    private_discrepancy_count: None = None
    finding_policy: str = 'Only issues derived from published category totals are disclosed. Private receipt findings and review notes are not published; this count is not a count of all discrepancies.'
    last_updated_at: datetime
    timestamp_basis: str = 'Snapshot calculation time, not a provider settlement or source-change timestamp.'


class LedgerPage(BaseModel):
    project_id: int
    items: list[LedgerEntry]
    total: int
    limit: int
    offset: int
    sort: Literal['date_desc', 'date_asc']
    calculated_at: datetime
