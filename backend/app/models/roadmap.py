"""Maintainer commitments and append-only history, independent of GitHub signals."""
from datetime import date, datetime
from sqlalchemy import BigInteger, String, Text, Date, DateTime, ForeignKey, ForeignKeyConstraint, UniqueConstraint, CheckConstraint, JSON, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base

STATES = "'planned','in_progress','submitted_for_review','delivered','cancelled'"


class ProjectRoadmapMilestone(Base):
    __tablename__ = 'project_roadmap_milestones'
    __table_args__ = (
        UniqueConstraint('id','project_id'),
        CheckConstraint('planned_start_date <= planned_end_date',name='ck_roadmap_dates'),
        CheckConstraint(f'status IN ({STATES})',name='ck_roadmap_status'),
        CheckConstraint('version > 0 AND display_order >= 0',name='ck_roadmap_version_order'),
        CheckConstraint("(status = 'delivered') = (actual_completion_date IS NOT NULL)",name='ck_roadmap_completion'),
    )
    id: Mapped[int] = mapped_column(BigInteger,primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey('projects.id',ondelete='RESTRICT'),index=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    deliverable_description: Mapped[str] = mapped_column(Text)
    planned_start_date: Mapped[date] = mapped_column(Date)
    planned_end_date: Mapped[date] = mapped_column(Date)
    actual_completion_date: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(24),default='planned')
    display_order: Mapped[int] = mapped_column(BigInteger,default=0)
    version: Mapped[int] = mapped_column(BigInteger,default=1)
    created_by: Mapped[int] = mapped_column(ForeignKey('users.id',ondelete='RESTRICT'))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),server_default=func.now(),onupdate=func.now())


class MilestoneGitHubEvidence(Base):
    __tablename__ = 'milestone_github_evidence'
    __table_args__ = (
        ForeignKeyConstraint(['milestone_id','project_id'],['project_roadmap_milestones.id','project_roadmap_milestones.project_id'],ondelete='RESTRICT'),
        ForeignKeyConstraint(['project_id','issue_snapshot_id'],['github_issue_snapshots.project_id','github_issue_snapshots.github_id'],ondelete='RESTRICT'),
        ForeignKeyConstraint(['project_id','pr_snapshot_id'],['github_pr_snapshots.project_id','github_pr_snapshots.github_id'],ondelete='RESTRICT'),
        ForeignKeyConstraint(['project_id','milestone_snapshot_id'],['github_milestone_snapshots.project_id','github_milestone_snapshots.github_id'],ondelete='RESTRICT'),
        UniqueConstraint('milestone_id','evidence_type','canonical_id'),
        CheckConstraint("(evidence_type='issue' AND issue_snapshot_id IS NOT NULL AND pr_snapshot_id IS NULL AND milestone_snapshot_id IS NULL) OR (evidence_type='pull_request' AND pr_snapshot_id IS NOT NULL AND issue_snapshot_id IS NULL AND milestone_snapshot_id IS NULL) OR (evidence_type='github_milestone' AND milestone_snapshot_id IS NOT NULL AND issue_snapshot_id IS NULL AND pr_snapshot_id IS NULL) OR (evidence_type='commit' AND issue_snapshot_id IS NULL AND pr_snapshot_id IS NULL AND milestone_snapshot_id IS NULL)",name='ck_roadmap_evidence_reference'),
    )
    id: Mapped[str] = mapped_column(String(36),primary_key=True)
    milestone_id: Mapped[int] = mapped_column(BigInteger,index=True)
    project_id: Mapped[int] = mapped_column(BigInteger)
    evidence_type: Mapped[str] = mapped_column(String(20))
    canonical_id: Mapped[str] = mapped_column(String(40))
    issue_snapshot_id: Mapped[int | None] = mapped_column(BigInteger)
    pr_snapshot_id: Mapped[int | None] = mapped_column(BigInteger)
    milestone_snapshot_id: Mapped[int | None] = mapped_column(BigInteger)
    linked_snapshot_json: Mapped[dict] = mapped_column(JSON)
    created_by: Mapped[int] = mapped_column(ForeignKey('users.id',ondelete='RESTRICT'))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),server_default=func.now())
    removed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    removed_by: Mapped[int | None] = mapped_column(ForeignKey('users.id',ondelete='RESTRICT'))


class MilestoneStatusHistory(Base):
    __tablename__ = 'milestone_status_history'
    __table_args__ = (UniqueConstraint('milestone_id','version'),)
    id: Mapped[str] = mapped_column(String(36),primary_key=True)
    milestone_id: Mapped[int] = mapped_column(ForeignKey('project_roadmap_milestones.id',ondelete='RESTRICT'),index=True)
    version: Mapped[int] = mapped_column(BigInteger)
    previous_status: Mapped[str | None] = mapped_column(String(24))
    new_status: Mapped[str] = mapped_column(String(24))
    actor_id: Mapped[int] = mapped_column(ForeignKey('users.id',ondelete='RESTRICT'))
    action: Mapped[str] = mapped_column(String(24))
    reason: Mapped[str] = mapped_column(String(2000))
    before_json: Mapped[dict] = mapped_column(JSON)
    after_json: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),server_default=func.now())
