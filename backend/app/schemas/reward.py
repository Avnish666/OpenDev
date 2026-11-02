from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator

class Benefit(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default='', max_length=2000)

class RewardCreate(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    name: str = Field(min_length=1, max_length=100)
    description: str = Field(min_length=1, max_length=5000)
    price_cents: int = Field(gt=0, le=9223372036854775807, strict=True)
    currency: Literal['USD'] = 'USD'
    benefits: list[Benefit] = Field(min_length=1, max_length=50)
    quantity_limit: int | None = Field(default=None, gt=0, le=9223372036854775807, strict=True)
    active: bool = True

class RewardPatch(RewardCreate):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, min_length=1, max_length=5000)
    price_cents: int | None = Field(default=None, gt=0, le=9223372036854775807, strict=True)
    currency: Literal['USD'] | None = None
    benefits: list[Benefit] | None = Field(default=None, min_length=1, max_length=50)
    active: bool | None = None

    @model_validator(mode='after')
    def reject_null(self):
        if any(getattr(self, k) is None for k in self.model_fields_set - {'quantity_limit'}):
            raise ValueError('Only quantity_limit may be null')
        return self

class RewardResponse(RewardCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    project_id: int
    created_at: datetime
    updated_at: datetime
