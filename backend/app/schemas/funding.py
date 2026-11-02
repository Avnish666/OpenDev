from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

class Checkout(BaseModel):
    model_config = ConfigDict(extra='forbid')
    tier_id: int = Field(gt=0)
    checkout_key: UUID

class Fulfill(BaseModel):
    model_config = ConfigDict(extra='forbid',str_strip_whitespace=True)
    note: str = Field(min_length=1,max_length=2000)


from datetime import datetime
from typing import Literal
from app.schemas.reward import Benefit

class RewardSnapshot(BaseModel):
    name: str
    description: str
    benefits: list[Benefit]

class EntitlementResponse(BaseModel):
    id: str
    status: Literal['granted', 'fulfilled', 'revoked']
    fulfillment_note: str

class ContributionResponse(BaseModel):
    id: str
    project_id: int
    tier_id: int
    amount_cents: int
    currency: Literal['USD']
    status: Literal['creating','created','cancelled','pending','denied','completed','refunded','reversed']
    order_id: str | None
    capture_id: str | None
    approval_url: str | None
    reward: RewardSnapshot
    created_at: datetime
    entitlement: EntitlementResponse | None
