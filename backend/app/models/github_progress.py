"""GitHub observations, separate from financial and deliverable records."""
from datetime import datetime
from sqlalchemy import BigInteger, String, Text, DateTime, ForeignKey, JSON, CheckConstraint, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class GitHubSyncRun(Base):
    __tablename__ = 'github_sync_runs'
    __table_args__ = (CheckConstraint("status IN ('running','completed','failed')", name='ck_github_sync_status'),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey('projects.id', ondelete='RESTRICT'), index=True)
    status: Mapped[str] = mapped_column(String(16))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    retry_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_code: Mapped[str | None] = mapped_column(String(40))
    counters: Mapped[dict] = mapped_column(JSON, default=dict)


class GitHubRepositorySnapshot(Base):
    __tablename__ = 'github_repository_snapshots'
    project_id: Mapped[int] = mapped_column(ForeignKey('projects.id', ondelete='RESTRICT'), primary_key=True)
    github_repo_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    metadata_json: Mapped[dict] = mapped_column(JSON)
    recent_commits: Mapped[list] = mapped_column(JSON)
    publicly_accessible: Mapped[bool] = mapped_column(Boolean, default=True)
    etag: Mapped[str | None] = mapped_column(String(500))
    last_synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class Observation:
    project_id: Mapped[int] = mapped_column(ForeignKey('projects.id', ondelete='RESTRICT'), primary_key=True)
    github_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, unique=True)
    number: Mapped[int] = mapped_column(BigInteger)
    title: Mapped[str] = mapped_column(Text)
    state: Mapped[str] = mapped_column(String(12))
    last_synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class GitHubMilestoneSnapshot(Observation, Base):
    __tablename__ = 'github_milestone_snapshots'
    description: Mapped[str | None] = mapped_column(Text)
    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    open_issues: Mapped[int] = mapped_column(BigInteger)
    closed_issues: Mapped[int] = mapped_column(BigInteger)


class GitHubIssueSnapshot(Observation, Base):
    __tablename__ = 'github_issue_snapshots'
    # Canonical external reference, not an FK: GitHub may delete a milestone.
    milestone_github_id: Mapped[int | None] = mapped_column(BigInteger)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class GitHubPullRequestSnapshot(Observation, Base):
    __tablename__ = 'github_pr_snapshots'
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    merged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
