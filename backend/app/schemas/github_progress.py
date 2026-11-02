from pydantic import AwareDatetime as datetime
from typing import Annotated, Literal
from pydantic import BaseModel, Field, ConfigDict

ID = Annotated[int, Field(strict=True, gt=0, le=9223372036854775807)]
Count = Annotated[int, Field(strict=True, ge=0)]


class RepositoryData(BaseModel):
    id: ID
    full_name: str = Field(pattern=r'^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$', max_length=200)
    private: Literal[False]
    description: str | None = Field(default=None, max_length=20000)
    default_branch: str = Field(min_length=1, max_length=255)
    updated_at: datetime
    pushed_at: datetime | None


class MilestoneData(BaseModel):
    id: ID
    number: ID
    title: str = Field(max_length=2000)
    description: str | None = Field(default=None, max_length=50000)
    state: Literal['open','closed']
    due_on: datetime | None
    open_issues: Count
    closed_issues: Count


class IssueData(BaseModel):
    id: ID
    number: ID
    title: str = Field(max_length=2000)
    state: Literal['open','closed']
    milestone: MilestoneData | None = None
    created_at: datetime
    updated_at: datetime
    closed_at: datetime | None


class PullData(BaseModel):
    id: ID
    number: ID
    title: str = Field(max_length=2000)
    state: Literal['open','closed']
    created_at: datetime
    updated_at: datetime
    merged_at: datetime | None


class RunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    status: Literal['running','completed','failed']
    started_at: datetime
    completed_at: datetime | None
    retry_at: datetime | None
    error_code: str | None
    counters: dict[str,int]


class SyncStatus(BaseModel):
    latest: RunResponse | None
    last_successful_sync_at: datetime | None
    stale: bool
    notice: str = 'GitHub observations are development signals, not proof of funded deliverable completion. A successful bounded incremental sync does not establish exhaustive repository coverage.'


class MilestoneResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    github_id: int
    number: int
    title: str
    description: str | None
    state: str
    due_date: datetime | None
    open_issues: int
    closed_issues: int
    last_synced_at: datetime


class ItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    github_id: int
    number: int
    title: str
    state: str
    created_at: datetime
    updated_at: datetime
    last_synced_at: datetime


class IssueResponse(ItemResponse):
    milestone_github_id: int | None
    closed_at: datetime | None


class PullResponse(ItemResponse):
    merged_at: datetime | None


class CommitResponse(BaseModel):
    sha: str
    committed_at: datetime


class ActivityResponse(BaseModel):
    sync: SyncStatus
    repository: RepositoryData | None
    counts: dict[str,int]
    issues: list[IssueResponse]
    pull_requests: list[PullResponse]
    recent_commits: list[CommitResponse]
    limit: int
    offset: int


class MilestonesResponse(BaseModel):
    sync: SyncStatus
    items: list[MilestoneResponse]
    total: int
