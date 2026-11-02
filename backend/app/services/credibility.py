"""Deterministic public track records, never reputation scores or financial writes."""
from datetime import date
import re
from fastapi import HTTPException
from sqlalchemy import select, func, or_
from app.models.user import User
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.roadmap import ProjectRoadmapMilestone as Milestone, MilestoneStatusHistory as History
from app.models.funding import Contribution, Entitlement
from app.models.expense import Expense
from app.models.expense_document import ExpenseDocument
from app.models.github_progress import GitHubRepositorySnapshot as Repo, GitHubIssueSnapshot as Issue, GitHubPullRequestSnapshot as Pull
from app.services import transparency, github_progress

SCOPE='Active public projects only. Draft, paused and completed projects are excluded, including when the requester is the owner.'
ATTRIBUTION='Outcome metrics cover owned projects only. Maintainer/collaborator participation is listed separately, without attributing the whole team’s results to an individual.'
DELIVERY_LIMIT='Delivery is a maintainer assertion, not independent verification. Original deadline means the earliest immutable creation record, including draft preparation; the first public deadline was not separately recorded.'


def identity(db,uid):
    user=db.get(User,uid)
    if not user:raise HTTPException(404,'Maintainer not found')
    return dict(user_id=user.id,github_id=user.github_id,username=user.username,
        avatar_url=f'https://avatars.githubusercontent.com/u/{user.github_id}' if user.github_id else None,
        github_profile_url='https://github.com/'+user.username if re.fullmatch(r'[A-Za-z0-9-]{1,39}',user.username) else None)


def projects_query(uid):
    membership=select(ProjectMember.project_id).where(ProjectMember.user_id==uid,ProjectMember.role.in_(['maintainer','collaborator']))
    return select(Project).where(Project.status=='active',or_(Project.owner_id==uid,Project.id.in_(membership)))


def roles(db,projects,uid):
    team_ids=[p.id for p in projects if p.owner_id!=uid]
    memberships=dict(db.execute(select(ProjectMember.project_id,ProjectMember.role).where(
        ProjectMember.project_id.in_(team_ids),ProjectMember.user_id==uid)).all()) if team_ids else {}
    return {p.id:'owner' if p.owner_id==uid else memberships[p.id] for p in projects}


def projects(db,uid,limit,offset,now):
    identity(db,uid)
    stmt=projects_query(uid)
    rows=db.scalars(stmt.order_by(Project.id).limit(limit).offset(offset)).all()
    membership_roles=roles(db,rows,uid)
    return dict(items=[dict(id=p.id,title=p.title,status=p.status,role=membership_roles[p.id],project_href=f'#/projects/{p.id}') for p in rows],
        total=db.scalar(select(func.count()).select_from(stmt.subquery())),limit=limit,offset=offset,calculated_at=now)


def owned_ids(uid):return select(Project.id).where(Project.owner_id==uid,Project.status=='active')


def iso_date(value):
    try:return date.fromisoformat(value) if isinstance(value,str) else None
    except ValueError:return None


def delivery_row(db,row,events=None,repository=...):
    if events is None:events=db.scalars(select(History).where(History.milestone_id==row.id).order_by(History.version)).all()
    original=None;actual=None;reopened=False;ever_delivered=False;linked={};delivery_links=None
    for event in events:
        if event.action=='created' and original is None:original=iso_date(event.after_json.get('planned_end_date'))
        if event.action=='evidence_linked':
            evidence=event.after_json.get('evidence',{})
            if evidence.get('id'):linked[evidence['id']]=True
        elif event.action=='evidence_removed':linked.pop(event.before_json.get('evidence',{}).get('id'),None)
        if event.previous_status=='delivered' and event.new_status!='delivered':reopened=True
        if event.action=='status_changed' and event.new_status=='delivered':
            ever_delivered=True;actual=iso_date(event.after_json.get('actual_completion_date'));delivery_links=len(linked)
    # Current delivery must be supported by immutable history and agree with its assertion.
    if row.status!='delivered':actual=None
    elif actual!=row.actual_completion_date:actual=None
    timing='not_currently_delivered' if row.status!='delivered' else 'unknown'
    if row.status=='delivered' and actual and original:timing='on_time' if actual<=original else 'late'
    repo=db.get(Repo,row.project_id) if repository is ... else repository
    if not repo or not repo.publicly_accessible:delivery_links=None
    return dict(milestone_id=row.id,project_id=row.project_id,title=row.title,status=row.status,original_deadline=original,
        current_deadline=row.planned_end_date,actual_completion_date=actual,timing=timing,ever_asserted_delivered=ever_delivered,reopened_after_delivery=reopened,
        evidence_links_at_delivery=delivery_links if row.status=='delivered' else None,updated_at=row.updated_at,
        project_href=f'#/projects/{row.project_id}',history_path=f'/api/roadmap/{row.id}/history')


def delivery_rows(db,rows):
    if not rows:return []
    histories=db.scalars(select(History).where(History.milestone_id.in_([r.id for r in rows])).order_by(History.milestone_id,History.version)).all()
    grouped={}
    for event in histories:grouped.setdefault(event.milestone_id,[]).append(event)
    repos={r.project_id:r for r in db.scalars(select(Repo).where(Repo.project_id.in_({r.project_id for r in rows})))}
    return [delivery_row(db,r,events=grouped.get(r.id,[]),repository=repos.get(r.project_id)) for r in rows]


def delivery_history(db,uid,limit,offset,now):
    identity(db,uid)
    stmt=select(Milestone).where(Milestone.project_id.in_(owned_ids(uid)))
    rows=db.scalars(stmt.order_by(Milestone.created_at.desc(),Milestone.id.desc()).limit(limit).offset(offset)).all()
    return dict(items=delivery_rows(db,rows),total=db.scalar(select(func.count()).select_from(stmt.subquery())),limit=limit,offset=offset,calculated_at=now)


def indicator(key,label,numerator,denominator,sample,now,updated,formula,limitations,links):
    return dict(key=key,label=label,numerator=numerator,denominator=denominator,sample_size=sample,
        state='unavailable' if numerator is None else 'insufficient_history' if sample==0 else 'recorded',formula=formula,
        calculated_at=now,last_updated_at=updated,limitations=limitations,source_links=links)


def profile(db,uid,now):
    user=identity(db,uid)
    participation={r:0 for r in ['owner','maintainer','collaborator']}
    visible=db.scalars(projects_query(uid).order_by(Project.id)).all()
    membership_roles=roles(db,visible,uid)
    for p in visible:participation[membership_roles[p.id]]+=1
    owned=[p for p in visible if p.owner_id==uid];ids=[p.id for p in owned]
    rows=db.scalars(select(Milestone).where(Milestone.project_id.in_(ids)).order_by(Milestone.id)).all() if ids else []
    history=delivery_rows(db,rows)
    updated=max((r.updated_at for r in rows),default=None)
    links=[f'/api/projects/{p.id}/roadmap' for p in owned]
    count=len(rows);delivered=sum(r['status']=='delivered' for r in history)
    known=sum(r['timing'] in ('on_time','late') for r in history)
    today=now.date()
    values=[('public_projects_owned','Public projects owned',len(owned),None,len(owned),'Count active projects whose owner_id equals this user ID.'),
        ('published_milestones','Published roadmap commitments',count,None,count,'Count roadmap milestones on owned active projects, once per milestone ID.'),
        ('asserted_delivered','Currently asserted delivered',delivered,count,count,'Count milestones currently in delivered status / all owned public commitments.'),
        ('ever_asserted_delivered','Commitments ever asserted delivered',sum(r['ever_asserted_delivered'] for r in history),count,count,'Count distinct milestones with any immutable delivered assertion, including subsequently reopened/cancelled milestones.'),
        ('overdue_planned','Currently overdue planned commitments',sum(r.status=='planned' and r.planned_end_date<today for r in rows),sum(r.status=='planned' for r in rows),sum(r.status=='planned' for r in rows),'Count planned milestones whose current end date is before today (UTC) / all planned milestones. This is a current-date measure, not an original-deadline success rate.'),
        ('delivered_on_time','Delivered by original deadline',sum(r['timing']=='on_time' for r in history),known,known,'Current delivered milestones with an immutable matching delivery date <= earliest recorded committed end date / delivered milestones with known comparable dates.'),
        ('delivered_late','Delivered after original deadline',sum(r['timing']=='late' for r in history),known,known,'Current delivered milestones with immutable matching delivery date > original end date / delivered milestones with known comparable dates.'),
        ('unknown_delivery_timing','Delivered with unknown timing',delivered-known,delivered,delivered,'Delivered assertions without a usable original deadline/matching immutable delivery date; never silently count them on time.'),
        ('cancelled','Cancelled commitments',sum(r.status=='cancelled' for r in rows),count,count,'Count currently cancelled milestones / all commitments.'),
        ('reopened','Commitments reopened after delivery',sum(r['reopened_after_delivery'] for r in history),count,count,'Count distinct milestones with any immutable delivered-to-other-status transition / all commitments.'),
        ('delivery_evidence','Delivered assertions with recorded GitHub support',sum(bool(r['evidence_links_at_delivery']) for r in history),sum(r['status']=='delivered' and r['evidence_links_at_delivery'] is not None for r in history),sum(r['status']=='delivered' and r['evidence_links_at_delivery'] is not None for r in history),'Delivered milestones with active GitHub links at their latest delivery assertion / delivered milestones whose repository evidence remains publicly available; unknown/private evidence excluded.'),
        ('independently_reviewed','Independently reviewed delivery',None,None,0,'Unavailable: no independent delivery review mechanism exists.')]
    delivery=[indicator(key,label,n,d,s,now,max((p.updated_at for p in owned),default=None) if key=='public_projects_owned' else None if key=='independently_reviewed' else updated,formula,[DELIVERY_LIMIT,SCOPE],links) for key,label,n,d,s,formula in values]
    rewards=[];pairs=db.execute(select(Entitlement,Contribution).join(Contribution,Entitlement.contribution_id==Contribution.id).where(Contribution.project_id.in_(ids))).all() if ids else []
    currencies={p.id:p.currency for p in owned}
    eligible=[(e,c) for e,c in pairs if c.status=='completed' and c.capture_id and c.currency==currencies[c.project_id] and e.status in ('granted','fulfilled')]
    issued=len(pairs);fulfilled=sum(e.status=='fulfilled' for e,c in eligible);updated_rewards=None
    reward_notes=['Sandbox entitlements only. Refunded/reversed/non-completed contributions and revoked/invalid entitlements are excluded from the fulfillment ratio. No backer identities or fulfillment notes are disclosed.', 'Fulfillment is a maintainer mark, not independent proof. Individual reward records and notes remain private; only aggregates are disclosed. No fulfillment deadline or status-change timestamp is stored; last_updated_at is unknown.']
    for key,label,n,d,s,formula in [
        ('issued','Entitlements issued',issued,None,issued,'Count distinct persisted entitlement IDs, including subsequently revoked records.'),
        ('fulfilled','Rewards marked fulfilled',fulfilled,len(eligible),len(eligible),'Eligible fulfilled entitlement IDs / all eligible granted-or-fulfilled IDs with completed captures.'),
        ('pending','Rewards pending fulfillment',len(eligible)-fulfilled,len(eligible),len(eligible),'Eligible granted entitlement IDs / all eligible IDs.'),
        ('excluded','Excluded/revoked entitlements',issued-len(eligible),issued,issued,'Issued minus currently eligible, including refunded/reversed or revoked records.'),
        ('overdue','Overdue rewards',None,None,0,'Unavailable: no explicit reward fulfillment deadlines exist.')]:
        rewards.append(indicator(key,label,n,d,s,now,updated_rewards,formula,reward_notes,[f'/api/maintainers/{uid}/credibility']))
    financial=[];github=[]
    for p in owned:
        summary=transparency.overview(db,p);s=summary['financial_summary']
        expenses=db.scalars(select(Expense).where(Expense.project_id==p.id,Expense.publication_status=='published')).all()
        last=db.scalar(select(func.max(Expense.updated_at)).where(Expense.project_id==p.id,Expense.publication_status=='published'))
        approval=db.scalar(select(func.max(ExpenseDocument.approved_at)).join(Expense).where(Expense.project_id==p.id,Expense.publication_status=='published',ExpenseDocument.publication_status=='published',ExpenseDocument.redacted_from_id.is_not(None),ExpenseDocument.approved_by.is_not(None)))
        last=max([t for t in [last,approval] if t],default=None)
        financial.append(dict(project_id=p.id,reporting_available=bool(expenses),currency=p.currency,published_reported_spending_cents=s['published_reported_spending_cents'],document_supported_expense_cents=s['expenses_with_documents_cents'],last_reporting_activity=last,
            metrics=[indicator('reporting_available','Published reporting available',int(bool(expenses)),1,len(expenses),now,last,'At least one published expense report exists for this project.', ['An empty reporting scope is insufficient history, not misconduct.'],[f'/api/projects/{p.id}/ledger']),
                indicator('document_coverage','Expenses with approved public evidence',s['expenses_with_documents_count'],s['published_expense_count'],s['published_expense_count'],now,last,'Published expenses with >=1 approved public redaction / published expense IDs, each counted once.', ['Private originals excluded. Supporting receipts do not prove vendor payment.'],[f'/api/projects/{p.id}/ledger']),
                indicator('public_findings','Unresolved public findings',summary['public_unresolved_discrepancy_count'],None,len(s['budget_variance']),now,last,'Count category overruns derived only from published financial records.', ['Private OCR/reviewer findings and their counts are withheld. An unresolved discrepancy is not proof of fraud.'],[f'/api/projects/{p.id}/transparency'])],notes=s['notes']))
        repo=db.get(Repo,p.id);available=bool(repo and repo.publicly_accessible and repo.github_repo_id==p.github_repo_id)
        status=github_progress.status(db,p.id);timestamp=status['last_successful_sync_at'] if available else None
        nissues=db.scalar(select(func.count()).select_from(Issue).where(Issue.project_id==p.id)) if available else 0
        closed=db.scalar(select(func.count()).select_from(Issue).where(Issue.project_id==p.id,Issue.state=='closed')) if available else None
        nprs=db.scalar(select(func.count()).select_from(Pull).where(Pull.project_id==p.id)) if available else 0
        merged=db.scalar(select(func.count()).select_from(Pull).where(Pull.project_id==p.id,Pull.merged_at.is_not(None))) if available else None
        github.append(dict(project_id=p.id,repository_name=repo.metadata_json['full_name'] if available else None,last_successful_sync_at=timestamp,stale=not available or status['stale'],
            metrics=[indicator(key,label,n,d,sample,now,timestamp,formula,['Repository/team activity is not personal authorship or proof of funded delivery. Deleted snapshots may be retained; commit sampling is incomplete.'],[f'/api/projects/{p.id}/github/activity'] if available else []) for key,label,n,d,sample,formula in [
                ('closed_issues','Observed closed issues',closed,nissues if available else None,nissues,'Closed non-PR issue snapshots / observed issue snapshots.'),
                ('merged_prs','Observed merged pull requests',merged,nprs if available else None,nprs,'PR snapshots with merged_at / observed PR snapshots; closed is not necessarily merged.'),
                ('sampled_commits','Recent default-branch commit sample',len(repo.recent_commits) if available else None,None,len(repo.recent_commits) if available else 0,'Count recent sampled commit SHAs, not a full history or productivity score.')]]))
    return dict(identity=user,calculated_at=now,attribution=ATTRIBUTION,scope=SCOPE,participation=participation,delivery=delivery,rewards=rewards,financial=financial,github=github,
        limitations=[DELIVERY_LIMIT,'No composite trust score, weights, fraud judgment or independent verification. Insufficient history is not poor performance.',
        'Metrics are calculated now from a read-only snapshot. Last source update may be unknown; calculation time is not a provider verification time.',
        'Public scope can shrink when a project becomes non-active. No project publication/ownership history exists, so outcomes reflect current owner attribution, not guaranteed historical ownership.',
        'Amounts stay per project/currency; exact partial refunds remain unavailable under the existing conservative policy.'])
