
from pydantic import BaseModel, Field, ConfigDict, model_validator
from typing import Literal


class BudgetAllocationCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True, extra="forbid")
    category: str = Field(min_length=2, max_length=100)
    allocated_cents: int = Field(ge=0, le=9223372036854775807, strict=True)


class ProjectCreate(BaseModel):
    github_repo: str = Field(
        min_length=3,
        max_length=200,
        description="GitHub owner/repository",
    )
    title: str = Field(min_length=3, max_length=150)
    description: str = Field(min_length=20)
    funding_goal_cents: int = Field(gt=0)
    currency: Literal["USD"] = "USD"
    budget: list[BudgetAllocationCreate] = Field(min_length=1)


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    owner_id: int
    github_repo_id: int
    github_repo_url: str
    title: str
    description: str
    funding_goal_cents: int
    currency: str
    status: str


class ProjectPatch(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    title: str | None = Field(default=None, min_length=3, max_length=150)
    description: str | None = Field(default=None, min_length=20, max_length=20000)
    funding_goal_cents: int | None = Field(default=None, gt=0, le=9223372036854775807, strict=True)
    budget: list[BudgetAllocationCreate] | None = Field(default=None, min_length=1, max_length=100)

    @model_validator(mode='after')
    def reject_null(self):
        if any(getattr(self, k) is None for k in self.model_fields_set):
            raise ValueError('Project fields cannot be null')
        return self

class MaintainerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    avatar_url: str | None

class ProjectDetail(ProjectResponse):
    budget: list[BudgetAllocationCreate]
    maintainers: list[MaintainerResponse]
    can_manage: bool
