"""One public read snapshot across development, ownership and existing accounting."""
from datetime import timedelta
from sqlalchemy import select, func, union_all
from app.models.project import Project
from app.models.roadmap import ProjectRoadmapMilestone as Milestone, MilestoneStatusHistory as History, MilestoneGitHubEvidence as Evidence
from app.models.github_progress import GitHubRepositorySnapshot as Repo, GitHubIssueSnapshot as Issue, GitHubPullRequestSnapshot as Pull, GitHubMilestoneSnapshot as GitHubMilestone
from app.services import transparency, credibility, github_progress, roadmap


def counts(rows,now):
    result={state:sum(row['status']==state for row in rows) for state in ['planned','in_progress','submitted_for_review','delivered','cancelled']}
    return dict(total=len(rows),**result,
        overdue_unfinished=sum(row['status'] not in ('delivered','cancelled') and row['current_deadline']<now.date() for row in rows),
        reopened=sum(row['reopened_after_delivery'] for row in rows),on_time=sum(row['timing']=='on_time' for row in rows),
        late=sum(row['timing']=='late' for row in rows),unknown_delivery_timing=sum(row['status']=='delivered' and row['timing']=='unknown' for row in rows))


def linked_freshness(db,project_id,repo,now,sync_stale):
    if not repo or not repo.publicly_accessible:return None
    statements=[]
    for model,ref in [(Issue,Evidence.issue_snapshot_id),(Pull,Evidence.pr_snapshot_id),(GitHubMilestone,Evidence.milestone_snapshot_id)]:
        statements.append(select(model.last_synced_at.label('observed')).join(Evidence,(Evidence.project_id==model.project_id)&(ref==model.github_id)).where(model.project_id==project_id,Evidence.removed_at.is_(None)))
    observed=db.scalar(select(func.min(union_all(*statements).subquery().c.observed)))
    commits=db.scalars(select(Evidence.canonical_id).where(Evidence.project_id==project_id,Evidence.evidence_type=='commit',Evidence.removed_at.is_(None))).all()
    if observed is None and not commits:return None
    sample={c['sha'] for c in repo.recent_commits}
    return bool(sync_stale or (observed and now-observed>timedelta(hours=6)) or any(sha not in sample for sha in commits) or (commits and now-repo.last_synced_at>timedelta(hours=6)))


def summary(db,project_id):
    project=transparency.public_project(db,project_id)
    now=db.scalar(select(func.transaction_timestamp()))
    # Batch the current owner's public milestones and immutable history, once.
    owned=db.scalars(select(Project).where(Project.owner_id==project.owner_id,Project.status=='active')).all()
    rows=db.scalars(select(Milestone).where(Milestone.project_id.in_([p.id for p in owned])).order_by(Milestone.id)).all()
    derived=credibility.delivery_rows(db,rows)
    own=[r for r in derived if r['project_id']==project_id]
    current=[r for r in rows if r.project_id==project_id]
    repo=db.get(Repo,project_id)
    available=bool(repo and repo.publicly_accessible and repo.github_repo_id==project.github_repo_id)
    sync=github_progress.status(db,project_id)
    activity=github_progress.public_activity(db,project_id) if available else None
    milestones=db.scalars(select(GitHubMilestone).where(GitHubMilestone.project_id==project_id).order_by(GitHubMilestone.number,GitHubMilestone.github_id).limit(10)).all() if available else []
    linked_issues=db.scalar(select(func.count(func.distinct(Evidence.canonical_id))).where(Evidence.project_id==project_id,Evidence.evidence_type=='issue',Evidence.removed_at.is_(None))) if available else None
    linked_merged=db.scalar(select(func.count(func.distinct(Pull.github_id))).join(Evidence,(Evidence.project_id==Pull.project_id)&(Evidence.pr_snapshot_id==Pull.github_id)).where(Pull.project_id==project_id,Pull.merged_at.is_not(None),Evidence.removed_at.is_(None))) if available else None
    changes=db.execute(select(History,Milestone.title).join(Milestone).where(Milestone.project_id==project_id).order_by(History.created_at.desc(),History.id.desc()).limit(10)).all()
    financial=transparency.overview(db,project)
    values=financial['financial_summary']
    financial_keys=['currency','gross_completed_funding_cents','refund_excluded_cents','reversal_excluded_cents','net_recorded_funding_cents','published_reported_spending_cents','funding_minus_reported_expenditure_cents','expenses_with_documents_count','expenses_with_documents_cents','published_expense_count','notes']
    timestamp=sync['last_successful_sync_at']
    return dict(project_id=project_id,github_repository_id=project.github_repo_id,calculated_at=now,
        roadmap_updated_at=max((r.updated_at for r in current),default=None),counts=counts(own,now),
        linked_issues=linked_issues,linked_merged_pull_requests=linked_merged,github_available=available,
        linked_evidence_stale=linked_freshness(db,project_id,repo,now,sync['stale']) if available else None,
        sync=dict(latest={k:getattr(sync['latest'],k) for k in ['status','started_at','completed_at','error_code']} if sync['latest'] else None,last_successful_sync_at=timestamp,stale=not available or sync['stale']),snapshot_age_seconds=max(0,int((now-timestamp).total_seconds())) if timestamp else None,
        activity=activity,github_milestones=milestones,
        delivery_history_preview=sorted(own,key=lambda r:(r['updated_at'],r['milestone_id']),reverse=True)[:10],
        recent_changes=[dict(**roadmap.history_view(h,False),milestone_id=h.milestone_id,title=title) for h,title in changes],
        owner=dict(identity=credibility.identity(db,project.owner_id),public_projects=len(owned),delivery=counts(derived,now),profile_href=f'#/maintainers/{project.owner_id}',scope=credibility.ATTRIBUTION+' '+credibility.SCOPE),
        financial={**{key:values[key] for key in financial_keys},'public_unresolved_discrepancy_count':financial['public_unresolved_discrepancy_count']},
        links=dict(roadmap=f'/api/projects/{project_id}/roadmap',financial=f'/api/projects/{project_id}/transparency',github=f'/api/projects/{project_id}/github/activity',owner=f'/api/maintainers/{project.owner_id}/credibility'),
        limitations=[credibility.DELIVERY_LIMIT,
            'Overdue unfinished = planned, in-progress or submitted commitments with current end date before today UTC. Delivered/cancelled are excluded.',
            'GitHub activity and delivery are separate observations/assertions, never independent certification or a completion percentage.',
            'Counts use retained snapshots and unique linked IDs. Deleted GitHub records may remain; an empty repository is not evidence of abandonment.',
            'GitHub visibility is checked during sync. If known private/unavailable, source activity and linked-source counts are withheld.',
            'Preview lists contain at most 10 records; commit activity is the existing recent sample. Full roadmap/ledger/profile views remain available.',
            'Last attempt, last success, internal roadmap update and calculation time are different timestamps; no live-update claim.',
            'Private OCR and reviewer findings are withheld. Public findings cover budget overruns only; receipt support does not verify payment.'])
