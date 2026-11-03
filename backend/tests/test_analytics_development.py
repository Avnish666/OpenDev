"""Public development contracts reuse immutable delivery/eligibility rules."""
from datetime import date,datetime,timezone,timedelta
from uuid import uuid4
import json,os
from pathlib import Path
import pytest
from sqlalchemy import select,func,event
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.roadmap import ProjectRoadmapMilestone as Milestone,MilestoneStatusHistory as History
from app.models.funding import Contribution,Entitlement
from app.models.github_progress import GitHubRepositorySnapshot as Repo,GitHubSyncRun as Run
from app.services import accountability,transparency
from test_accountability import ac,contribution,receipt
from test_credibility import milestone
from test_github_progress import gh,sync,ISSUE,PULL
from test_analytics import get
from test_phase4_performance import measure


def test_states_and_overlapping_indicators(ac):
    for status in ['planned','in_progress','submitted_for_review','cancelled']:
        milestone(ac,status=status)
    milestone(ac,completed='2026-10-30',status='delivered')
    milestone(ac,completed='2026-10-30',status='in_progress',reopened=True)
    d=get(ac).json()['development'];c=d['counts']
    assert c['total']==6 and sum(c[k] for k in ['planned','in_progress','submitted_for_review','delivered','cancelled'])==6
    assert c['in_progress']==2 and c['overdue_unfinished']==4 and c['reopened']==1
    assert c['cancelled']==1 and c['on_time']==1
    assert sum(r['overdue'] for r in d['milestones'])==4


@pytest.mark.parametrize('actual,timing,delay',[('2026-10-30','on_time',-1),('2026-10-31','on_time',0),('2026-11-01','late',1)])
def test_deadline_dates_and_differences(ac,actual,timing,delay):
    milestone(ac,current='2026-12-01',completed=actual,status='delivered')
    row=get(ac).json()['development']['milestones'][0]
    assert row['original_deadline']=='2026-10-31' and row['current_deadline']=='2026-12-01'
    assert row['deadline_shift_days']==31 and row['delivery_delay_days']==delay and row['timing']==timing
    assert row['revision_count']==4 and row['deadline_revision_count']==1


def test_missing_history_never_fabricates_original_or_actual_date(ac):
    row=Milestone(project_id=ac.p.id,title='Missing history',description='Synthetic',deliverable_description='Synthetic',planned_start_date=date(2026,1,1),planned_end_date=date(2026,11,1),actual_completion_date=date(2026,11,1),status='delivered',version=1,created_by=ac.users[0].id)
    ac.db.add(row);ac.db.commit()
    d=get(ac).json()['development'];r=d['milestones'][0]
    assert r['original_deadline'] is None and r['actual_completion_date'] is None
    assert r['deadline_shift_days'] is None and r['delivery_delay_days'] is None
    assert r['timing']=='unknown' and d['counts']['unknown_delivery_timing']==1


def test_due_today_utc_and_cancelled_not_overdue(ac):
    today=ac.db.scalar(select(func.transaction_timestamp())).date().isoformat()
    milestone(ac,original=today);milestone(ac,status='cancelled')
    d=get(ac).json()['development'];assert d['counts']['overdue_unfinished']==0
    assert not any(r['overdue'] for r in d['milestones'])


def test_independent_history_pagination_and_stable_order(ac):
    rows=[milestone(ac) for _ in range(4)]
    first=get(ac,limit=2).json();second=get(ac,limit=2,milestone_offset=2).json()
    assert [r['milestone_id'] for r in second['development']['milestones']]==[r.id for r in rows[2:]]
    assert second['development']['offset']==2 and second['expense_offset']==0
    assert first['financial']==second['financial'] or first['financial']['published_reported_spending_cents']==second['financial']['published_reported_spending_cents']
    assert first['development']['counts']==second['development']['counts']
    assert get(ac,milestone_offset=999).json()['development']['milestones']==[]


@pytest.mark.parametrize('offset',[-1,10001])
def test_history_offset_validation(ac,offset):assert get(ac,milestone_offset=offset).status_code==422


def test_github_observed_classification_and_limits(gh):
    ac,s=gh;s['issues'].append(dict(ISSUE,id=202,number=8,state='closed'))
    s['pulls'].extend([dict(PULL,id=302,number=9,merged_at=None),dict(PULL,id=303,number=10,state='open',merged_at=None)])
    assert sync(ac).json()['status']=='completed'
    d=get(ac).json()['development'];g=d['github']
    assert g['counts']==dict(issues_open=1,issues_closed=1,pull_requests_open=1,pull_requests_closed=2,pull_requests_merged=1,milestones_open=1,milestones_closed=0)
    assert len(g['recent_commits'])==1 and g['exhaustive'] is False
    assert g['counts']==d['github_counts'] and g['repository_name']=='owner/repo'
    assert 'bounded' in ' '.join(g['limitations']) and 'deleted' in ' '.join(g['limitations']).lower()
    s['issues']=[];s['pulls']=[];sync(ac)
    assert get(ac).json()['development']['github']['counts']['issues_open']==1


def test_failed_sync_preserves_last_success_and_staleness(gh):
    ac,s=gh;sync(ac);old=get(ac).json()['development']['github']
    s['code']=500;sync(ac);g=get(ac).json()['development']['github']
    assert g['counts']==old['counts'] and g['sync']['stale'] is True
    assert g['sync']['last_successful_sync_at']==old['sync']['last_successful_sync_at']
    assert g['sync']['latest']['status']=='failed' and 'counters' not in g['sync']['latest']


@pytest.mark.parametrize('kind',['private','identity','missing'])
def test_inaccessible_github_suppresses_retained_source_data(gh,kind):
    ac,s=gh;sync(ac);repo=ac.db.get(Repo,ac.p.id)
    if kind=='private':repo.publicly_accessible=False
    elif kind=='identity':repo.github_repo_id=99999
    else:ac.db.delete(repo)
    ac.db.commit();g=get(ac).json()['development']['github']
    assert g['available'] is False and g['counts'] is None and g['repository_name'] is None
    assert not g['recent_commits'] and not g['issues'] and not g['pull_requests']


def test_missing_github_is_unknown_not_zero(ac):
    g=get(ac).json()['development']['github']
    assert g['counts'] is None and g['sync']['stale'] is True and g['observed_at'] is None


def test_owner_team_attribution_and_project_reward_scope(ac):
    extra=Project(owner_id=ac.users[0].id,github_repo_id=987,github_repo_url='https://github.com/owner/extra',title='Another owned',description='Synthetic',funding_goal_cents=100,currency='USD',status='active')
    ac.db.add(extra);ac.db.flush();ac.db.add(ProjectMember(project_id=ac.other.id,user_id=ac.users[0].id,role='collaborator'))
    c=contribution(ac);c.project_id=extra.id;ac.db.add(Entitlement(id=str(uuid4()),contribution_id=c.id,status='fulfilled'));ac.db.commit()
    d=get(ac).json()['maintainer']
    assert d['participation']['owner']==2 and d['participation']['collaborator']==1
    assert next(m for m in d['rewards'] if m['key']=='fulfilled')['numerator']==1
    assert next(m for m in d['project_rewards'] if m['key']=='fulfilled')['numerator']==0
    assert 'owned' in d['attribution']


def test_reward_eligibility_and_overlapping_exclusions_private_notes(ac):
    secrets=[]
    for status,ent,captured in [('completed','fulfilled',True),('completed','granted',True),('refunded','revoked',True),('reversed','fulfilled',True),('completed','revoked',True),('completed','fulfilled',False)]:
        c=contribution(ac,status=status,capture=captured);eid=str(uuid4());secrets += [eid,c.id,c.capture_id] if c.capture_id else [eid,c.id]
        ac.db.add(Entitlement(id=eid,contribution_id=c.id,status=ent,fulfillment_note='PRIVATE_BACKER_NOTE'))
    ac.db.commit();r=get(ac);m={v['key']:v for v in r.json()['maintainer']['project_rewards']}
    assert m['issued']['numerator']==6 and m['eligible']['numerator']==2
    assert (m['fulfilled']['numerator'],m['fulfilled']['denominator'])==(1,2)
    assert m['pending']['numerator']==1 and m['excluded']['numerator']==4
    assert m['revoked']['numerator']==2 and m['refunded']['numerator']==1 and m['reversed']['numerator']==1
    assert m['overdue']['state']=='unavailable'
    assert all(v not in r.text for v in secrets+['PRIVATE_BACKER_NOTE'])


def test_no_reward_history_explicit_state(ac):
    metrics=get(ac).json()['maintainer']['project_rewards']
    assert all(v['state'] in ('unavailable','insufficient_history') for v in metrics)


def test_private_and_cross_project_milestones_never_enter_scope(ac):
    private=Project(owner_id=ac.users[0].id,github_repo_id=888,github_repo_url='https://github.com/owner/private',title='PRIVATE_PROJECT',description='Synthetic',funding_goal_cents=100,currency='USD',status='draft')
    ac.db.add(private);ac.db.commit();old=ac.p
    for project in (private,ac.other):
        ac.p=project;row=milestone(ac);row.title='PRIVATE_MILESTONE';ac.db.commit()
    ac.p=old
    for user in (None,ac.users[0]):
        ac.identity[0]=user;r=get(ac)
        assert 'PRIVATE_' not in r.text and r.json()['development']['total']==0
    ac.p=private;assert get(ac).status_code==404


def test_readonly_source_records(ac):
    m=milestone(ac);c=contribution(ac)
    before=(m.version,m.status,ac.e.amount_cents,c.status,ac.db.scalar(select(func.count()).select_from(History)))
    get(ac);ac.db.refresh(m);ac.db.refresh(c);ac.db.refresh(ac.e)
    assert before==(m.version,m.status,ac.e.amount_cents,c.status,ac.db.scalar(select(func.count()).select_from(History)))


def test_batched_public_financial_formula_parity(ac):
    contribution(ac,'completed',6000);contribution(ac,'refunded',2000)
    with accountability.read_snapshot(ac.db) as db:
        p=db.get(Project,ac.p.id);context=accountability.public_sources(db,[p])
        assert accountability.snapshot(db,p,None)==accountability.snapshot(db,p,None,public_context=context)


def test_representative_development_and_constant_owner_queries(gh):
    ac,s=gh;sync(ac);milestone(ac)
    path=f'/api/projects/{ac.p.id}/analytics/overview';baseline=measure(ac,path)
    for i in range(99):milestone(ac,current='2026-12-01')
    s['issues']=[dict(ISSUE,id=10000+i,number=100+i) for i in range(200)];s['pulls']=[dict(PULL,id=20000+i,number=400+i,merged_at=None if i%2 else PULL['merged_at']) for i in range(100)];s['paged_rows']=True
    sync(ac);large=measure(ac,path)
    assert large['query_count']==baseline['query_count']
    for i in range(5):ac.db.add(Project(owner_id=ac.users[0].id,github_repo_id=90000+i,github_repo_url=f'https://github.com/owner/extra-{i}',title='Synthetic',description='Synthetic',funding_goal_cents=100,currency='USD',status='active'))
    ac.db.commit();owners=measure(ac,path)
    assert owners['query_count']==large['query_count']
    target=os.getenv('PHASE6_DEVELOPMENT_PERFORMANCE_FILE')
    if target:Path(target).write_text(json.dumps(dict(baseline=baseline,representative=large,six_owned_projects=owners,source=dict(milestones=100,issue_snapshots=201,pr_snapshots=101,commit_sample=1)),indent=2))
