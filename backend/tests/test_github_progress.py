from copy import deepcopy
from datetime import datetime, timezone
from uuid import uuid4
import threading
from concurrent.futures import ThreadPoolExecutor
import httpx
import pytest
from sqlalchemy import select, func
from app.services import github_progress as service
from app.models.github_progress import GitHubSyncRun as Run, GitHubIssueSnapshot as Issue, GitHubPullRequestSnapshot as Pull, GitHubMilestoneSnapshot as Milestone
from test_accountability import ac, contribution

DATE='2026-11-01T12:00:00Z'
MILESTONE=dict(id=101,number=1,title='Beta',description='Observed target',state='open',due_on=None,open_issues=1,closed_issues=0)
ISSUE=dict(id=201,number=2,title='Work item',state='open',milestone=MILESTONE,created_at=DATE,updated_at=DATE,closed_at=None)
PULL=dict(id=301,number=3,title='Change',state='closed',created_at=DATE,updated_at=DATE,merged_at=DATE)


@pytest.fixture
def gh(ac,monkeypatch):
    monkeypatch.delenv('GITHUB_SYNC_TOKEN',raising=False)
    state=dict(calls=[],repo={'id':ac.p.github_repo_id,'full_name':'owner/repo','private':False,'default_branch':'main','updated_at':DATE,'pushed_at':DATE},milestones=[deepcopy(MILESTONE)],issues=[deepcopy(ISSUE),dict(ISSUE,id=301,number=3,pull_request={})],pulls=[deepcopy(PULL)],code=None,pages=False)
    def handler(request):
        state['calls'].append(request)
        assert request.url.host=='api.github.com'
        assert request.headers['X-GitHub-Api-Version']=='2022-11-28'
        if state.get('block'):
            state['entered'].set(); assert state['release'].wait(10)
        if state.get('timeout'):raise httpx.ReadTimeout('synthetic timeout')
        if state['code']:return httpx.Response(state['code'],headers={'Retry-After':'120'})
        path=request.url.path
        if path.startswith('/repositories/'):
            if state.get('conditional') and request.headers.get('if-none-match'): return httpx.Response(304)
            return httpx.Response(200,json=state['repo'],headers={'etag':'"repo-v1"'})
        kind=path.rsplit('/',1)[-1]
        if kind=='commits':return httpx.Response(200,json=[{'sha':'a'*40,'commit':{'committer':{'date':DATE}}}])
        if state.get('endless') and kind=='issues':return httpx.Response(200,json=state[kind],headers={'Link':'<https://api.github.com/next>; rel="next"'})
        if state['pages'] and kind=='issues':
            if request.url.params.get('page')=='1':return httpx.Response(200,json=state[kind],headers={'Link':'<https://evil.invalid/next>; rel="next"'})
            return httpx.Response(200,json=[dict(ISSUE,id=202,number=4)])
        return httpx.Response(200,json=state[kind])
    monkeypatch.setattr(service,'client',service.GitHubClient(httpx.MockTransport(handler)))
    return ac,state


def sync(ac):return ac.client.post(f'/api/projects/{ac.p.id}/github/sync')
def activity(ac):return ac.client.get(f'/api/projects/{ac.p.id}/github/activity')


def test_initial_repeat_classification_merge_and_conditional(gh):
    ac,s=gh
    assert sync(ac).json()['status']=='completed'
    s['conditional']=True
    assert sync(ac).json()['status']=='completed'
    data=activity(ac).json()
    assert data['counts']==dict(issues_open=1,issues_closed=0,pull_requests_open=0,pull_requests_closed=1,pull_requests_merged=1)
    for model in [Issue,Pull,Milestone]:assert ac.db.scalar(select(func.count()).select_from(model))==1
    assert data['recent_commits'][0]['sha']=='a'*40
    assert data['sync']['last_successful_sync_at'] and not data['sync']['stale']
    assert any(r.headers.get('if-none-match') for r in s['calls'])
    assert any('since' in r.url.params for r in s['calls'])


def test_updates_and_rename(gh):
    ac,s=gh;sync(ac)
    s['repo']['full_name']='renamed/project';s['milestones'][0]['state']='closed';s['milestones'][0]['title']='Changed milestone'
    assert sync(ac).json()['status']=='completed'
    assert activity(ac).json()['repository']['full_name']=='renamed/project'
    assert any(r.url.path=='/repos/renamed/project/issues' for r in s['calls'])
    assert ac.client.get(f'/api/projects/{ac.p.id}/github/milestones').json()['items'][0]['title']=='Changed milestone'
    ac.db.refresh(ac.p);assert ac.p.github_repo_url=='https://github.com/test/project'


@pytest.mark.parametrize('code,error',[(404,'REPOSITORY_UNAVAILABLE'),(429,'RATE_LIMITED'),(500,'GITHUB_UNAVAILABLE')])
def test_failures_preserve_snapshots(gh,code,error):
    ac,s=gh;sync(ac);s['code']=code
    run=sync(ac).json();assert run['status']=='failed' and run['error_code']==error
    assert ac.db.scalar(select(func.count()).select_from(Issue))==1
    assert activity(ac).json()['sync']['stale']
    if code==429:
        count=len(s['calls']);assert sync(ac).status_code==429;assert len(s['calls'])==count
        ac.identity[0]=ac.users[3]
        assert ac.client.post(f'/api/projects/{ac.other.id}/github/sync').status_code==429
        assert len(s['calls'])==count
    if code==404:
        ac.identity[0]=None;assert activity(ac).status_code==404


@pytest.mark.parametrize('change',[{'id':999},{'private':True},{'id':'1'}])
def test_identity_private_and_malformed(gh,change):
    ac,s=gh;sync(ac);s['repo'].update(change)
    assert sync(ac).json()['status']=='failed'
    assert ac.db.scalar(select(func.count()).select_from(Issue))==1


def test_atomic_late_malformed_and_pagination(gh):
    ac,s=gh;s['pages']=True
    assert sync(ac).json()['status']=='completed'
    assert activity(ac).json()['counts']['issues_open']==2
    s['milestones'][0]['title']='Must not persist';s['pulls']=[{'bad':'data'}]
    assert sync(ac).json()['error_code']=='MALFORMED_RESPONSE'
    assert ac.client.get(f'/api/projects/{ac.p.id}/github/milestones').json()['items'][0]['title']=='Beta'
    assert all(r.url.host=='api.github.com' for r in s['calls'])


def test_concurrent_sync_and_interrupted_attempt(gh):
    ac,s=gh;s.update(block=True,entered=threading.Event(),release=threading.Event())
    with ThreadPoolExecutor(max_workers=1) as pool:
        request=pool.submit(sync,ac);assert s['entered'].wait(5)
        assert sync(ac).status_code==409
        s['release'].set();assert request.result().json()['status']=='completed'
    s['block']=False
    ac.db.add(Run(id=str(uuid4()),project_id=ac.p.id,status='running',started_at=datetime.now(timezone.utc),counters={}))
    ac.db.commit()
    assert sync(ac).json()['status']=='completed'
    assert ac.db.scalar(select(func.count()).select_from(Run).where(Run.error_code=='INTERRUPTED'))==1


@pytest.mark.parametrize('actor',[2,3])
def test_permissions_and_csrf(gh,actor):
    ac,s=gh;ac.identity[0]=ac.users[actor];assert sync(ac).status_code==403
    ac.identity[0]=ac.users[0]
    assert ac.client.post(f'/api/projects/{ac.p.id}/github/sync',headers={'Origin':'https://evil.invalid'}).status_code==403
    assert s['calls']==[]


def test_visibility_and_financial_invariance(gh):
    ac,s=gh;payment=contribution(ac);before=ac.client.get(f'/api/projects/{ac.p.id}/accountability').json()
    sync(ac);ac.db.refresh(payment);assert payment.status=='completed' and payment.amount_cents==2000
    ac.db.refresh(ac.e);assert ac.e.amount_cents==1000 and ac.e.evidence_status=='unverified'
    after=ac.client.get(f'/api/projects/{ac.p.id}/accountability').json()
    assert before['published_reported_spending_cents']==after['published_reported_spending_cents']
    ac.identity[0]=None;assert activity(ac).status_code==200
    for state in ['draft','paused','completed']:
        ac.p.status=state;ac.db.commit()
        for suffix in ['activity','milestones','sync-status']:assert ac.client.get(f'/api/projects/{ac.p.id}/github/{suffix}').status_code==404


@pytest.mark.parametrize('flag,error',[('timeout','INVALID_OR_UNAVAILABLE_RESPONSE'),('endless','PAGE_LIMIT')])
def test_bounded_requests_and_atomic_initial_failure(gh,flag,error):
    ac,s=gh;s[flag]=True
    assert sync(ac).json()['error_code']==error
    assert ac.db.scalar(select(func.count()).select_from(Issue))==0
    assert len(s['calls'])<=7


def test_revoked_visibility_survives_subsequent_failure(gh):
    ac,s=gh;sync(ac);s['repo']['private']=True
    assert sync(ac).json()['error_code']=='REPOSITORY_NOT_PUBLIC'
    s['code']=500;sync(ac)
    ac.identity[0]=None;assert activity(ac).status_code==404
    ac.identity[0]=ac.users[0];s['code']=None;s['repo']['private']=False;sync(ac)
    ac.identity[0]=None;assert activity(ac).status_code==200


def test_maintainer_and_anonymous_authorization(gh):
    from app.main import app
    from app.core.auth import get_current_user
    ac,s=gh;ac.identity[0]=ac.users[1]
    assert sync(ac).json()['status']=='completed'
    app.dependency_overrides.pop(get_current_user)
    assert sync(ac).status_code==401


def test_optional_token_never_persisted_or_returned(gh,monkeypatch):
    ac,s=gh;monkeypatch.setenv('GITHUB_SYNC_TOKEN','synthetic-private-progress-token')
    response=sync(ac)
    assert response.json()['status']=='completed'
    assert all(r.headers.get('authorization')=='Bearer synthetic-private-progress-token' for r in s['calls'])
    assert 'synthetic-private-progress-token' not in response.text+activity(ac).text
    assert 'synthetic-private-progress-token' not in str(ac.db.scalars(select(Run)).all())
