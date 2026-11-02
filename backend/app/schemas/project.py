
from pydantic import BaseModel, Field, ConfigDict
from typing import Literal


class BudgetAllocationCreate(BaseModel):
    category: str = Field(min_length=2, max_length=100)
    allocated_cents: int = Field(ge=0)


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
