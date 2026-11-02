from datetime import date, datetime, timezone, timedelta
from uuid import uuid4
from sqlalchemy import select, func
import pytest
from app.models.user import User
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.roadmap import ProjectRoadmapMilestone as Milestone, MilestoneStatusHistory as History
from app.models.funding import Entitlement
from app.models.github_progress import GitHubRepositorySnapshot as Repo, GitHubSyncRun as Run
from test_accountability import ac, contribution, receipt, decision, verification
from test_transparency import redacted
from test_github_progress import gh, sync


def profile(ac,uid=None):
    result=ac.client.get(f'/api/maintainers/{uid or ac.users[0].id}/credibility');assert result.status_code==200,result.text
    assert result.headers['cache-control']=='no-store'
    return result.json()


def metrics(data,section):return {item['key']:item for item in data[section]}


def milestone(ac,original='2026-10-31',current=None,completed=None,status='planned',reopened=False):
    actual=date.fromisoformat(completed) if completed else None
    row=Milestone(project_id=ac.p.id,title='Synthetic promise',description='Synthetic commitment',deliverable_description='Publish a documented release',planned_start_date=date(2026,1,1),planned_end_date=date.fromisoformat(current or original),actual_completion_date=actual if status=='delivered' else None,status=status,version=1,created_by=ac.users[0].id)
    ac.db.add(row);ac.db.flush();version=0;previous=None
    def event(action,new,after):
        nonlocal version,previous
        version+=1
        ac.db.add(History(id=str(uuid4()),milestone_id=row.id,version=version,previous_status=previous,new_status=new,actor_id=ac.users[0].id,action=action,reason='Synthetic immutable public history',before_json={'status':previous},after_json=after));previous=new
    event('created','planned',{'planned_end_date':original,'status':'planned'})
    if current:event('edited','planned',{'planned_end_date':current,'status':'planned'})
    if completed:
        event('status_changed','in_progress',{'status':'in_progress'});event('status_changed','submitted_for_review',{'status':'submitted_for_review'})
        event('status_changed','delivered',{'status':'delivered','actual_completion_date':completed})
    if reopened:event('status_changed','in_progress',{'status':'in_progress','actual_completion_date':None})
    elif status=='cancelled':event('status_changed','cancelled',{'status':'cancelled'})
    row.version=version;ac.db.commit();return row


def test_new_user_insufficient_history_not_a_zero_score(ac):
    user=User(username='new-user',github_id=9999);ac.db.add(user);ac.db.commit()
    data=profile(ac,user.id)
    assert data['financial']==[] and data['github']==[]
    assert all(m['state'] in ('insufficient_history','unavailable') for m in data['delivery']+data['rewards'])
    assert metrics(data,'rewards')['fulfilled']['denominator']==0
    assert 'score' not in data and 'email' not in data['identity']


@pytest.mark.parametrize('actual,expected',[('2026-10-30','on_time'),('2026-10-31','on_time'),('2026-11-01','late')])
def test_original_deadline_timing(ac,actual,expected):
    milestone(ac,completed=actual,status='delivered')
    m=metrics(profile(ac),'delivery');assert m['delivered_'+expected]['numerator']==1
    assert m['asserted_delivered']['numerator']==1
    data=ac.client.get(f'/api/maintainers/{ac.users[0].id}/delivery-history').json()
    assert data['items'][0]['independently_reviewed'] is False
    assert data['items'][0]['actual_completion_date']==actual


def test_changed_deadline_cannot_improve_delivery_timing(ac):
    milestone(ac,original='2026-10-01',current='2026-12-01',completed='2026-11-01',status='delivered')
    m=metrics(profile(ac),'delivery')
    assert m['delivered_on_time']['numerator']==0 and m['delivered_late']['numerator']==1
    history=ac.client.get(f'/api/maintainers/{ac.users[0].id}/delivery-history').json()['items'][0]
    assert history['original_deadline']=='2026-10-01' and history['current_deadline']=='2026-12-01'


def test_reopened_cancelled_and_overdue(ac):
    milestone(ac,completed='2026-10-30',status='in_progress',reopened=True)
    milestone(ac,status='cancelled');milestone(ac)
    m=metrics(profile(ac),'delivery')
    assert m['reopened']['numerator']==1 and m['cancelled']['numerator']==1
    assert m['asserted_delivered']['numerator']==0 and m['ever_asserted_delivered']['numerator']==1
    assert m['overdue_planned']['numerator']==1
    assert m['delivered_on_time']['sample_size']==0


def test_attribution_and_multiple_projects(ac):
    milestone(ac,completed='2026-10-30',status='delivered')
    for actor,role in [(1,'maintainer'),(2,'collaborator')]:
        data=profile(ac,ac.users[actor].id)
        assert data['participation'][role]==1
        assert metrics(data,'delivery')['asserted_delivered']['numerator']==0
        page=ac.client.get(f'/api/maintainers/{ac.users[actor].id}/projects').json()
        assert page['items'][0]['role']==role
    extra=Project(owner_id=ac.users[0].id,github_repo_id=999,github_repo_url='https://github.com/owner/second',title='Second project',description='Another public project',funding_goal_cents=100,currency='USD',status='active')
    ac.db.add(extra);ac.db.commit()
    assert metrics(profile(ac),'delivery')['public_projects_owned']['numerator']==2


def test_reward_ratio_refunds_revocations_and_backer_privacy(ac):
    for status,ent in [('completed','fulfilled'),('completed','granted'),('refunded','revoked'),('reversed','fulfilled'),('pending','granted')]:
        c=contribution(ac,status=status);ac.db.add(Entitlement(id=str(uuid4()),contribution_id=c.id,status=ent,fulfillment_note='PRIVATE_BACKER_NOTE'))
    ac.db.commit()
    data=profile(ac);m=metrics(data,'rewards')
    assert m['issued']['numerator']==5
    assert (m['fulfilled']['numerator'],m['fulfilled']['denominator'])==(1,2)
    assert m['pending']['numerator']==1 and m['excluded']['numerator']==3
    assert m['overdue']['numerator'] is None and m['fulfilled']['last_updated_at'] is None
    assert 'PRIVATE_BACKER_NOTE' not in str(data)
    assert 'contribution_id' not in str(data) and 'capture_id' not in str(data)


def test_financial_coverage_once_per_expense_and_private_notes(ac):
    original,record=receipt(ac);decision(ac,verification(ac)['findings'][0])
    redacted(ac,original);redacted(ac,original)
    data=profile(ac)
    financial=data['financial'][0];m={v['key']:v for v in financial['metrics']}
    assert (m['document_coverage']['numerator'],m['document_coverage']['denominator'])==(1,1)
    assert financial['document_supported_expense_cents']==1000 and financial['last_reporting_activity']
    for hidden in [original.id,record.id,original.storage_key,'Synthetic private review','extracted_json','finding_snapshot']:
        assert hidden not in str(data)


@pytest.mark.parametrize('state',['draft','paused','completed'])
def test_private_scope_even_with_owner_cookie(ac,state):
    from app.services.session_service import create_session, SESSION_COOKIE
    ac.client.cookies.set(SESSION_COOKIE,create_session(ac.db,ac.users[0].id))
    milestone(ac);ac.p.status=state;ac.db.commit()
    data=profile(ac)
    assert data['financial']==[] and data['github']==[]
    assert ac.client.get(f'/api/maintainers/{ac.users[0].id}/projects').json()['total']==0
    assert ac.client.get(f'/api/maintainers/{ac.users[0].id}/delivery-history').json()['total']==0


def test_missing_and_stale_github_evidence(gh):
    ac,s=gh
    assert profile(ac)['github'][0]['stale']
    sync(ac)
    data=profile(ac)['github'][0]
    assert not data['stale'] and next(m for m in data['metrics'] if m['key']=='merged_prs')['numerator']==1
    run=ac.db.scalar(select(Run).where(Run.status=='completed'));run.completed_at=datetime.now(timezone.utc)-timedelta(days=1);ac.db.commit()
    assert profile(ac)['github'][0]['stale']
    repo=ac.db.get(Repo,ac.p.id);repo.publicly_accessible=False;ac.db.commit()
    data=profile(ac)['github'][0]
    assert data['repository_name'] is None and all(m['numerator'] is None for m in data['metrics'])


def test_pagination_public_access_and_invariance(ac):
    for _ in range(3):milestone(ac)
    c=contribution(ac);before=(ac.e.amount_cents,c.status,ac.db.scalar(select(func.count()).select_from(History)))
    ac.identity[0]=None;data=profile(ac)
    first=ac.client.get(f'/api/maintainers/{ac.users[0].id}/delivery-history?limit=1').json()
    second=ac.client.get(f'/api/maintainers/{ac.users[0].id}/delivery-history?limit=1&offset=1').json()
    assert first['total']==3 and first['items'][0]['milestone_id']!=second['items'][0]['milestone_id']
    ac.db.refresh(ac.e);ac.db.refresh(c)
    assert before==(ac.e.amount_cents,c.status,ac.db.scalar(select(func.count()).select_from(History)))
    assert ac.client.get('/api/maintainers/9999999/credibility').status_code==404
    assert ac.client.get(f'/api/maintainers/{ac.users[0].id}/projects?limit=101').status_code==422
    assert ac.client.post(f'/api/maintainers/{ac.users[0].id}/credibility',json={'score':100}).status_code==405


def test_evidence_is_measured_at_delivery_not_after_it(gh):
    from test_roadmap import create, link, action, ok, REASON
    ac,s=gh;ok(sync(ac))
    row=create(ac);row=ok(link(ac,row));row=ok(action(ac,row,'in_progress'))
    row=ok(action(ac,row,'submitted_for_review'));row=ok(action(ac,row,'delivered'))
    row=ok(link(ac,row,'pull_request','301'))
    history=ac.client.get(f'/api/maintainers/{ac.users[0].id}/delivery-history').json()['items'][0]
    assert history['evidence_links_at_delivery']==1  # later PR link is not retroactive support
    assert history['independently_reviewed'] is False
    assert metrics(profile(ac),'delivery')['independently_reviewed']['numerator'] is None


def test_missing_original_history_is_unknown_not_on_time(ac):
    row=Milestone(project_id=ac.p.id,title='Legacy row',description='Synthetic',deliverable_description='Legacy delivery assertion',planned_start_date=date(2026,1,1),planned_end_date=date(2026,12,1),actual_completion_date=date(2026,11,1),status='delivered',version=1,created_by=ac.users[0].id)
    ac.db.add(row);ac.db.commit()
    m=metrics(profile(ac),'delivery')
    assert m['asserted_delivered']['numerator']==1
    assert m['unknown_delivery_timing']['numerator']==1 and m['delivered_on_time']['numerator']==0
