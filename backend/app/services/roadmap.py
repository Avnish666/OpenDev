"""Roadmap assertions never alter payment, expense or GitHub source records."""
from datetime import datetime, timezone, timedelta
from uuid import uuid4
from pydantic import ValidationError
from fastapi import HTTPException
from sqlalchemy import select, func
from app.models.roadmap import ProjectRoadmapMilestone as Milestone, MilestoneGitHubEvidence as Evidence, MilestoneStatusHistory as History
from app.models.github_progress import GitHubRepositorySnapshot as Repo, GitHubIssueSnapshot as Issue, GitHubPullRequestSnapshot as Pull, GitHubMilestoneSnapshot as GitHubMilestone
from app.models.project import Project
from app.schemas.roadmap import Commitment
from app.services.project_management import project_for, can_manage, commit
from app.services import github_progress

FIELDS=['title','description','deliverable_description','planned_start_date','planned_end_date','display_order']
TRANSITIONS={'planned':{'in_progress','cancelled'},'in_progress':{'planned','submitted_for_review','cancelled'},'submitted_for_review':{'in_progress','delivered','cancelled'},'delivered':{'in_progress'},'cancelled':{'planned'}}
TYPES={'issue':(Issue,'issue_snapshot_id','issues'),'pull_request':(Pull,'pr_snapshot_id','pull'),'github_milestone':(GitHubMilestone,'milestone_snapshot_id','milestone')}


def snapshot(row):
    return {k:(getattr(row,k).isoformat() if hasattr(getattr(row,k),'isoformat') else getattr(row,k)) for k in FIELDS+['status','actual_completion_date']}


def authorize_project(db,pid,user=None,write=False):
    project=project_for(db,pid,user,write=write)
    if not write and project.status!='active' and not can_manage(db,project,user):raise HTTPException(404,'Project not found')
    return project


def get(db,mid,user,write=False):
    row=db.get(Milestone,mid)
    if not row:raise HTTPException(404,'Roadmap milestone not found')
    authorize_project(db,row.project_id,user,write)
    if write:
        row=db.scalar(select(Milestone).where(Milestone.id==mid).with_for_update().execution_options(populate_existing=True))
    return row


def check_version(row,data):
    if row.version!=data.expected_version:raise HTTPException(409,'Milestone changed; refresh before retrying')


def audit(db,row,user,action,reason,before,after):
    db.add(History(id=str(uuid4()),milestone_id=row.id,version=row.version,previous_status=before.get('status'),new_status=row.status,
        actor_id=user.id,action=action,reason=reason,before_json=before,after_json=after,created_at=db.scalar(select(func.clock_timestamp()))))


def create(db,pid,user,data):
    authorize_project(db,pid,user,True)
    row=Milestone(project_id=pid,created_by=user.id,status='planned',version=1,**data.model_dump())
    db.add(row);db.flush()
    audit(db,row,user,'created','Roadmap commitment created.',{},snapshot(row));commit(db);db.refresh(row)
    return row


def edit(db,mid,user,data):
    row=get(db,mid,user,True);check_version(row,data)
    values=data.model_dump(exclude_unset=True,exclude={'expected_version','reason'})
    if not values:raise HTTPException(422,'Provide at least one roadmap field')
    if row.status!='planned' and set(values)-{'display_order'}:raise HTTPException(409,'Reopen and return to planned before changing commitments')
    before=snapshot(row)
    try:Commitment.model_validate({**{k:getattr(row,k) for k in FIELDS},**values})
    except ValidationError:raise HTTPException(422,'Invalid milestone fields or date range') from None
    for key,value in values.items():setattr(row,key,value)
    row.version+=1;audit(db,row,user,'edited',data.reason,before,snapshot(row));commit(db);db.refresh(row)
    return row


def change_status(db,mid,user,data):
    row=get(db,mid,user,True);check_version(row,data)
    if data.status not in TRANSITIONS[row.status]:raise HTTPException(409,'Invalid milestone status transition')
    if data.status in ('submitted_for_review','delivered') and not db.scalar(select(func.count()).select_from(Evidence).where(Evidence.milestone_id==mid,Evidence.removed_at.is_(None))):
        raise HTTPException(409,'Link GitHub evidence before submission or delivery')
    before=snapshot(row);row.status=data.status
    row.actual_completion_date=datetime.now(timezone.utc).date() if data.status=='delivered' else None
    row.version+=1;audit(db,row,user,'status_changed',data.reason,before,snapshot(row));commit(db);db.refresh(row)
    return row


def resolve(db,pid,kind,canonical):
    repo=db.get(Repo,pid);project=db.get(Project,pid)
    if not repo or repo.github_repo_id!=project.github_repo_id or not repo.publicly_accessible:
        raise HTTPException(409,'Synchronize a valid public linked repository first')
    if kind=='commit':
        source=next((c for c in repo.recent_commits if c['sha']==canonical),None)
        if source is None:raise HTTPException(422,'Commit is not in this project’s synchronized sample')
        return None,dict(number=None,state=None,merged=None,observed_at=repo.last_synced_at.isoformat(),repo_name=repo.metadata_json['full_name'],sha=canonical)
    model,_,_=TYPES[kind]
    source=db.get(model,(pid,int(canonical)))
    if source is None:raise HTTPException(422,'Evidence is not a synchronized item in this project')
    return source,dict(number=source.number,state=source.state,merged=bool(source.merged_at) if kind=='pull_request' else None,
        observed_at=source.last_synced_at.isoformat(),repo_name=repo.metadata_json['full_name'])


def link(db,mid,user,data):
    row=get(db,mid,user,True);check_version(row,data)
    source,frozen=resolve(db,row.project_id,data.evidence_type,data.canonical_id)
    old=db.scalar(select(Evidence).where(Evidence.milestone_id==mid,Evidence.evidence_type==data.evidence_type,Evidence.canonical_id==data.canonical_id))
    if old and old.removed_at is None:raise HTTPException(409,'Evidence already linked')
    values=dict(linked_snapshot_json=frozen,removed_at=None,removed_by=None)
    if source:values[TYPES[data.evidence_type][1]]=source.github_id
    if old:
        for key,value in values.items():setattr(old,key,value)
        evidence=old
    else:
        evidence=Evidence(id=str(uuid4()),milestone_id=mid,project_id=row.project_id,evidence_type=data.evidence_type,canonical_id=data.canonical_id,created_by=user.id,**values)
        db.add(evidence)
    row.version+=1
    audit(db,row,user,'evidence_linked',data.reason,{'status':row.status},{'status':row.status,'evidence':{'id':evidence.id,'type':data.evidence_type,'canonical_id':data.canonical_id,'snapshot':frozen}})
    commit(db);db.refresh(row);return row


def unlink(db,mid,eid,user,data):
    row=get(db,mid,user,True);check_version(row,data)
    evidence=db.scalar(select(Evidence).where(Evidence.id==eid,Evidence.milestone_id==mid,Evidence.removed_at.is_(None)))
    if not evidence:raise HTTPException(404,'Evidence link not found')
    if row.status in ('submitted_for_review','delivered') and db.scalar(select(func.count()).select_from(Evidence).where(Evidence.milestone_id==mid,Evidence.removed_at.is_(None)))<=1:
        raise HTTPException(409,'Reopen milestone before removing its last supporting link')
    evidence.removed_at=datetime.now(timezone.utc);evidence.removed_by=user.id;row.version+=1
    audit(db,row,user,'evidence_removed',data.reason,{'status':row.status,'evidence':{'id':eid,'canonical_id':evidence.canonical_id,'type':evidence.evidence_type}}, {'status':row.status})
    commit(db);db.refresh(row);return row


def evidence_view(db,link,user):
    repo=db.get(Repo,link.project_id);project=db.get(Project,link.project_id)
    hidden=not repo or not repo.publicly_accessible
    if hidden and not can_manage(db,project,user):
        return dict(id=link.id,evidence_type=link.evidence_type,canonical_id=None,url=None,state=None,merged=None,snapshot_available=False,stale=True,last_observed_at=None)
    frozen=link.linked_snapshot_json
    if link.evidence_type=='commit':
        current=next((c for c in repo.recent_commits if c['sha']==link.canonical_id),None) if repo else None
        state=None;merged=None;observed=repo.last_synced_at if current else datetime.fromisoformat(frozen['observed_at']);number=None
    else:
        source=db.get(TYPES[link.evidence_type][0],(link.project_id,int(link.canonical_id)))
        current=source;state=source.state if source else frozen['state'];merged=bool(source.merged_at) if source and link.evidence_type=='pull_request' else frozen['merged']
        observed=source.last_synced_at if source else datetime.fromisoformat(frozen['observed_at']);number=source.number if source else frozen['number']
    name=repo.metadata_json['full_name'] if repo else frozen['repo_name']
    suffix='commit/'+link.canonical_id if link.evidence_type=='commit' else TYPES[link.evidence_type][2]+'/'+str(number)
    stale=hidden or current is None or github_progress.status(db,link.project_id)['stale'] or datetime.now(timezone.utc)-observed>timedelta(hours=6)
    return dict(id=link.id,evidence_type=link.evidence_type,canonical_id=link.canonical_id,url='https://github.com/'+name+'/'+suffix,
        state=state,merged=merged,snapshot_available=current is not None,stale=stale,last_observed_at=observed)


def view(db,row,user):
    links=db.scalars(select(Evidence).where(Evidence.milestone_id==row.id,Evidence.removed_at.is_(None)).order_by(Evidence.created_at,Evidence.id)).all()
    evidence=[evidence_view(db,link,user) for link in links]
    signals={'linked_issues':0,'closed_issues':0,'linked_pull_requests':0,'merged_pull_requests':0,'linked_github_milestones':0,'closed_github_milestones':0,'linked_commits':0}
    for item in evidence:
        kind=item['evidence_type']
        if kind=='issue':signals['linked_issues']+=1;signals['closed_issues']+=int(item['state']=='closed')
        elif kind=='pull_request':signals['linked_pull_requests']+=1;signals['merged_pull_requests']+=int(item['merged'] is True)
        elif kind=='github_milestone':signals['linked_github_milestones']+=1;signals['closed_github_milestones']+=int(item['state']=='closed')
        else:signals['linked_commits']+=1
    return dict(**{k:getattr(row,k) for k in FIELDS+['id','project_id','status','actual_completion_date','version','created_by','created_at','updated_at']},evidence=evidence,development_signals=signals)


def history(db,row,user,limit,offset):
    manager=can_manage(db,db.get(Project,row.project_id),user)
    rows=db.scalars(select(History).where(History.milestone_id==row.id).order_by(History.version.desc()).limit(limit).offset(offset)).all()
    return [history_view(r,manager) for r in rows]


def history_view(r,manager=False):
    allowed=set(FIELDS+['status','actual_completion_date'])
    return dict(id=r.id,version=r.version,previous_status=r.previous_status,new_status=r.new_status,actor_id=r.actor_id,action=r.action,reason=r.reason,
        before=r.before_json if manager else {k:v for k,v in r.before_json.items() if k in allowed},
        after=r.after_json if manager else {k:v for k,v in r.after_json.items() if k in allowed},created_at=r.created_at)
