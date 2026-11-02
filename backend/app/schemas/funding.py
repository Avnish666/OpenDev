from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

class Checkout(BaseModel):
    model_config = ConfigDict(extra='forbid')
    tier_id: int = Field(gt=0)
    checkout_key: UUID

class Fulfill(BaseModel):
    model_config = ConfigDict(extra='forbid',str_strip_whitespace=True)
    note: str = Field(min_length=1,max_length=2000)
