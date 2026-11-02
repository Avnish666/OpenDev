from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.core.auth import get_current_user, get_optional_user
from app.core.database import get_db
from app.models.user import User
from app.models.github_progress import GitHubMilestoneSnapshot as Milestone, GitHubIssueSnapshot as Issue, GitHubPullRequestSnapshot as Pull, GitHubRepositorySnapshot as Repo
from app.routers.auth import require_trusted_origin
from app.routers.expenses import RecordID
from app.schemas.github_progress import RunResponse, SyncStatus, ActivityResponse, MilestonesResponse
from app.services import github_progress as service, accountability

router=APIRouter(prefix='/api/projects/{project_id}/github',tags=['GitHub progress'])


@router.post('/sync',response_model=RunResponse,dependencies=[Depends(require_trusted_origin)])
def sync(project_id: RecordID,db: Session=Depends(get_db),user: User=Depends(get_current_user)):
    return service.sync(db,project_id,user)


@router.get('/sync-status',response_model=SyncStatus)
def status(project_id: RecordID,db: Session=Depends(get_db),user: User | None=Depends(get_optional_user)):
    with accountability.read_snapshot(db) as reader:
        service.read_project(reader,project_id,user,status_only=True)
        return service.status(reader,project_id)


@router.get('/activity',response_model=ActivityResponse)
def activity(project_id: RecordID,limit: int=Query(20,ge=1,le=100),offset: int=Query(0,ge=0),db: Session=Depends(get_db),user: User | None=Depends(get_optional_user)):
    with accountability.read_snapshot(db) as reader:
        service.read_project(reader,project_id,user)
        counts={}
        for model,prefix in [(Issue,'issues'),(Pull,'pull_requests')]:
            for state in ('open','closed'):
                counts[prefix+'_'+state]=reader.scalar(select(func.count()).select_from(model).where(model.project_id==project_id,model.state==state))
        counts['pull_requests_merged']=reader.scalar(select(func.count()).select_from(Pull).where(Pull.project_id==project_id,Pull.merged_at.is_not(None)))
        repo=reader.get(Repo,project_id)
        return dict(sync=service.status(reader,project_id),repository=repo.metadata_json if repo else None,counts=counts,
            issues=reader.scalars(select(Issue).where(Issue.project_id==project_id).order_by(Issue.updated_at.desc(),Issue.github_id).limit(limit).offset(offset)).all(),
            pull_requests=reader.scalars(select(Pull).where(Pull.project_id==project_id).order_by(Pull.updated_at.desc(),Pull.github_id).limit(limit).offset(offset)).all(),
            recent_commits=repo.recent_commits if repo else [],limit=limit,offset=offset)


@router.get('/milestones',response_model=MilestonesResponse)
def milestones(project_id: RecordID,limit: int=Query(20,ge=1,le=100),offset: int=Query(0,ge=0),db: Session=Depends(get_db),user: User | None=Depends(get_optional_user)):
    with accountability.read_snapshot(db) as reader:
        service.read_project(reader,project_id,user)
        return dict(sync=service.status(reader,project_id),total=reader.scalar(select(func.count()).select_from(Milestone).where(Milestone.project_id==project_id)),
            items=reader.scalars(select(Milestone).where(Milestone.project_id==project_id).order_by(Milestone.number,Milestone.github_id).limit(limit).offset(offset)).all())
