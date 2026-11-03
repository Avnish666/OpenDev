"""Public snapshot adapters; delivery/eligibility rules remain in Phase 4 services."""
from datetime import timedelta
from fastapi import HTTPException
from sqlalchemy import select, func
from app.models.github_progress import GitHubRepositorySnapshot as Repo, GitHubIssueSnapshot as Issue, GitHubPullRequestSnapshot as Pull, GitHubMilestoneSnapshot as GitHubMilestone
from app.services import credibility, github_progress, progress

LIMITATIONS = [
    'Retained synchronized snapshots are not complete repository lifetime totals. Initial collections are bounded; deleted records may remain.',
    'Commits are a recent default-branch sample, not complete history or personal productivity. No comparable time windows exist for an activity trend.',
    'Issue closure and PR merge are development evidence, not certified delivery. Closed PR counts include merged PRs; merged is an overlapping subset.',
    'Visibility is checked at sync time, not continuously. Per-record observations can be old even after an incremental sync.'
]


def github(db, project, now):
    repo = db.get(Repo, project.id)
    sync = github_progress.status(db, project.id)
    available = bool(repo and repo.publicly_accessible and repo.github_repo_id == project.github_repo_id)
    for model in (Issue, Pull, GitHubMilestone):
        if available and db.scalar(select(func.count()).select_from(model).where(model.project_id == project.id)) > 10000:
            raise HTTPException(413, 'GitHub analytics scope exceeds capacity')
    timestamp = sync['last_successful_sync_at']
    public_sync = dict(latest={k:getattr(sync['latest'],k) for k in ['status','started_at','completed_at','error_code']} if sync['latest'] else None,
        last_successful_sync_at=timestamp, stale=not available or sync['stale'])
    result = dict(available=available, repository_name=repo.metadata_json['full_name'] if available else None,
        counts=None, sync=public_sync, observed_at=repo.last_synced_at if available else None,
        snapshot_age_seconds=max(0,int((now-timestamp).total_seconds())) if timestamp else None,
        issues=[],pull_requests=[],milestones=[],recent_commits=[],limitations=LIMITATIONS)
    if available:
        activity = github_progress.public_activity(db, project.id)
        counts = activity['counts']
        for state, count in db.execute(select(GitHubMilestone.state,func.count()).where(GitHubMilestone.project_id==project.id).group_by(GitHubMilestone.state)):
            counts['milestones_'+state] = count
        for state in ('open','closed'):counts.setdefault('milestones_'+state,0)
        result.update(counts=counts,issues=activity['issues'],pull_requests=activity['pull_requests'],
            milestones=db.scalars(select(GitHubMilestone).where(GitHubMilestone.project_id==project.id).order_by(GitHubMilestone.number,GitHubMilestone.github_id).limit(10)).all(),
            recent_commits=activity['recent_commits'][:30])
    return result


def dataset(db,project,now,derived,limit,offset):
    own = [r for r in derived if r['project_id']==project.id]
    rows = []
    for row in own[offset:offset+limit]:
        original, current, actual = row['original_deadline'],row['current_deadline'],row['actual_completion_date']
        rows.append(dict(**row,overdue=bool(progress.counts([row],now)['overdue_unfinished']),
            deadline_shift_days=(current-original).days if original else None,
            delivery_delay_days=(actual-original).days if actual and original else None))
    gh = github(db,project,now)
    return dict(counts=progress.counts(own,now),milestones=rows,total=len(own),limit=limit,offset=offset,
        github=gh,github_counts=gh['counts'],last_successful_sync_at=gh['sync']['last_successful_sync_at'],github_stale=gh['sync']['stale'])
