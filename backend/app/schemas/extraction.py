"""Private, evidence-backed observations. Never a payment approval."""
from datetime import date, datetime
from typing import Annotated, Generic, Literal, TypeVar
from pydantic import BaseModel, ConfigDict, Field, model_validator

T = TypeVar('T')
Confidence = Literal['high', 'medium', 'low', 'unknown']
Cents = Annotated[int, Field(ge=0, le=9223372036854775807, strict=True)]
FiniteFloat = Annotated[float, Field(allow_inf_nan=False)]


class Evidence(BaseModel):
    model_config = ConfigDict(extra='forbid')
    page: int = Field(ge=1, le=5)
    snippet: str = Field(max_length=160)
    bbox: list[FiniteFloat] | None = Field(default=None, min_length=4, max_length=4)
    coordinates: Literal['pdf_points', 'image_pixels'] | None = None


class Observed(BaseModel, Generic[T]):
    model_config = ConfigDict(extra='forbid')
    value: T | None = None
    confidence: Confidence = 'unknown'
    evidence: list[Evidence] = Field(default_factory=list, max_length=2)

    @model_validator(mode='after')
    def require_supported_observation(self):
        if self.value is None and self.confidence != 'unknown':
            raise ValueError('A missing value must have unknown confidence')
        if self.value is not None and (not self.evidence or self.confidence == 'unknown'):
            raise ValueError('Identified values require source evidence and confidence')
        return self


class LineItem(BaseModel):
    description: str = Field(max_length=160)
    amount_cents: int = Field(ge=0, le=9223372036854775807)
    confidence: Confidence
    evidence: Evidence


class ExtractedReceipt(BaseModel):
    model_config = ConfigDict(extra='forbid')
    vendor_name: Observed[Annotated[str, Field(min_length=1, max_length=120)]] = Field(default_factory=Observed)
    invoice_number: Observed[Annotated[str, Field(min_length=1, max_length=80)]] = Field(default_factory=Observed)
    document_date: Observed[date] = Field(default_factory=Observed)
    currency: Observed[Annotated[str, Field(pattern=r'^[A-Z]{3}$')]] = Field(default_factory=Observed)
    subtotal_cents: Observed[Cents] = Field(default_factory=Observed)
    tax_cents: Observed[Cents] = Field(default_factory=Observed)
    total_cents: Observed[Cents] = Field(default_factory=Observed)
    discount_cents: Observed[Cents] = Field(default_factory=Observed)
    amount_paid_cents: Observed[Cents] = Field(default_factory=Observed)
    amount_due_cents: Observed[Cents] = Field(default_factory=Observed)
    previous_balance_cents: Observed[Cents] = Field(default_factory=Observed)
    payment_status: Observed[Literal['paid', 'unpaid', 'partially_paid']] = Field(default_factory=Observed)
    line_items: list[LineItem] = Field(default_factory=list, max_length=100)
    extraction_method: Literal['pdf_text', 'tesseract', 'mixed', 'no_text']
    pages_processed: int = Field(ge=1, le=5)
    uncertainties: list[str] = Field(default_factory=list, max_length=30)


class Finding(BaseModel):
    finding_code: str
    severity: Literal['info', 'warning']
    reported_value: str | int | None = None
    extracted_value: str | int | None = None
    explanation: str
    evidence_reference: dict
    review_status: Literal['human_review_required'] = 'human_review_required'


class TriggerExtraction(BaseModel):
    model_config = ConfigDict(extra='forbid')
    retry: bool = Field(default=False, strict=True)


class AttemptResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    status: str
    processing_error_code: str | None
    started_at: datetime
    completed_at: datetime | None


class ExtractionResponse(BaseModel):
    id: str
    expense_document_id: str
    extraction_status: Literal['pending','processing','completed','failed']
    extraction_version: str
    extracted_json: ExtractedReceipt | None
    findings_json: list[Finding]
    reported_expense: dict
    comparison_is_stale: bool
    processing_error_code: str | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    attempts: list[AttemptResponse]
    human_review_required: Literal[True] = True
    notice: str = 'Extraction and discrepancy flags are unverified observations, not proof of payment or fraud.'
