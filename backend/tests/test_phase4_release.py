"""Phase 4 HTTP integration: cookie auth and disposable PostgreSQL; GitHub mocked."""
import os
from datetime import datetime, timezone, timedelta
from sqlalchemy import select, func, event
from app.main import app
from app.core.auth import get_current_user, get_optional_user
from app.models.funding import Contribution
from app.models.roadmap import MilestoneStatusHistory as History
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.routers import projects
from app.services import project_management
from test_accountability import ac
from test_github_progress import gh
from test_release_journey import login, ok
from test_roadmap import REASON


def test_cookie_authenticated_development_journey(gh, monkeypatch):
    ac,state=gh
    app.dependency_overrides.pop(get_current_user)
    app.dependency_overrides.pop(get_optional_user)
    client=ac.client;login(client,monkeypatch,ac.users[0])
    async def repository(repo_name,github_user_id):
        assert repo_name=='owner/release' and github_user_id==ac.users[0].github_id
        return {'id':9000,'url':'https://github.com/owner/release'}
    monkeypatch.setattr(projects,'verify_repository_ownership',repository)
    monkeypatch.setattr(project_management,'verify_repository_ownership',repository)
    body={'github_repo':'owner/release','title':'Development journey','description':'Synthetic integration project',
          'funding_goal_cents':10000,'budget':[{'category':'Development','allocated_cents':10000}]}
    project=ok(client.post('/api/projects',json=body),201);pid=project['id']
    today=datetime.now(timezone.utc).date()
    original=(today-timedelta(days=1)).isoformat();revised=(today+timedelta(days=7)).isoformat()
    commitment=dict(title='Synthetic release',description='<script>untrusted()</script>',
        deliverable_description='Publish a documented beta package',planned_start_date=(today-timedelta(days=7)).isoformat(),planned_end_date=original)
    row=ok(client.post(f'/api/projects/{pid}/roadmap',json=commitment),201);mid=row['id']
    # Signed-out draft privacy, including child histories/dependencies and aggregate endpoints.
    ok(client.post('/api/auth/logout'))
    for path in [f'/api/projects/{pid}/roadmap',f'/api/roadmap/{mid}/history',f'/api/projects/{pid}/roadmap/dependencies',
                 f'/api/projects/{pid}/progress-summary',f'/api/projects/{pid}/github/activity']:
        assert client.get(path).status_code==404
    login(client,monkeypatch,ac.users[0]);ok(client.post(f'/api/projects/{pid}/publish'))
    state['repo'].update(id=9000,full_name='owner/release')
    run=ok(client.post(f'/api/projects/{pid}/github/sync'));assert run['status']=='completed'
    activity=ok(client.get(f'/api/projects/{pid}/github/activity'))
    assert len(activity['issues'])==len(activity['pull_requests'])==len(activity['recent_commits'])==1
    assert len(ok(client.get(f'/api/projects/{pid}/github/milestones'))['items'])==1
    for kind,canonical in [('issue','201'),('pull_request','301'),('github_milestone','101'),('commit','a'*40)]:
        row=ok(client.post(f'/api/roadmap/{mid}/evidence',json={'expected_version':row['version'],'reason':REASON,'evidence_type':kind,'canonical_id':canonical}))
    assert row['status']=='planned' and row['actual_completion_date'] is None
    assert client.patch(f'/api/roadmap/{mid}',json={'expected_version':row['version'],'planned_end_date':revised}).status_code==422
    if os.getenv('PHASE4_BROWSER_JOURNEY')=='1':
        from phase4_browser_support import browser_schedule
        previous_version=row['version']
        browser_schedule(ac,monkeypatch,pid,mid,revised)
        row=next(r for r in ok(client.get(f'/api/projects/{pid}/roadmap'))['items'] if r['id']==mid)
        assert row['planned_end_date']==revised and row['version']==previous_version+1
    else:
        row=ok(client.patch(f'/api/roadmap/{mid}',json={'expected_version':row['version'],'reason':REASON,'planned_end_date':revised}))
    for status in ['in_progress','submitted_for_review','delivered']:
        row=ok(client.post(f'/api/roadmap/{mid}/status',json={'expected_version':row['version'],'reason':REASON,'status':status}))
    assert row['actual_completion_date']==today.isoformat()
    public=ok(client.get(f'/api/projects/{pid}/progress-summary'))
    assert public['counts']['delivered']==public['counts']['late']==1
    assert public['counts']['on_time']==0 and public['linked_merged_pull_requests']==1
    profile=ok(client.get(f'/api/maintainers/{ac.users[0].id}/credibility'))
    delivery={m['key']:m for m in profile['delivery']}
    assert delivery['delivered_late']['numerator']==1
    history=ok(client.get(f'/api/roadmap/{mid}/history'))
    assert next(h for h in history if h['action']=='created')['after']['planned_end_date']==original
    expected_reason='Browser confirmed revised public commitment' if os.getenv('PHASE4_BROWSER_JOURNEY')=='1' else REASON
    assert next(h for h in history if h['action']=='edited')['reason']==expected_reason
    assert ac.db.scalar(select(func.count()).select_from(History).where(History.milestone_id==mid))==len(history)
    assert ac.db.scalar(select(func.count()).select_from(Contribution))==0
    ac.db.refresh(ac.e);assert ac.e.amount_cents==1000
    ok(client.post('/api/auth/logout'));client.cookies.clear()
    visitor=ok(client.get(f'/api/projects/{pid}/progress-summary'))
    assert visitor['counts']==public['counts']
    assert visitor['delivery_history_preview'][0]['independently_reviewed'] is False
    for path in [f'/api/projects/{pid}/progress-summary',f'/api/projects/{pid}/roadmap',f'/api/roadmap/{mid}/history',
                 f'/api/projects/{pid}/github/activity',f'/api/maintainers/{ac.users[0].id}/credibility']:
        response=client.get(path);assert response.status_code==200
        assert response.headers['cache-control']=='no-store'
        for forbidden in ['storage_key','extracted_json','token_hash','synthetic-private-github-token','capture_id','email']:
            assert forbidden not in response.text
    assert client.patch(f'/api/roadmap/{mid}',json={'expected_version':row['version'],'reason':REASON,'title':'Unauthorized'}).status_code==401
    assert client.post(f'/api/projects/{pid}/github/sync').status_code==401


def test_team_project_page_membership_query_count_is_bounded(ac):
    uid=ac.users[1].id
    def measure():
        statements=[]
        def capture(*args):statements.append(1)
        event.listen(ac.engine,'before_cursor_execute',capture)
        try:
            response=ac.client.get(f'/api/maintainers/{uid}/projects?limit=100')
            assert response.status_code==200
            assert all(row['role']=='maintainer' for row in response.json()['items'])
        finally:event.remove(ac.engine,'before_cursor_execute',capture)
        return len(statements)
    baseline=measure()
    for i in range(12):
        p=Project(owner_id=ac.users[0].id,github_repo_id=10000+i,github_repo_url='https://github.com/owner/synthetic',title='Synthetic',description='Synthetic',funding_goal_cents=10000,currency='USD',status='active')
        ac.db.add(p);ac.db.flush();ac.db.add(ProjectMember(project_id=p.id,user_id=uid,role='maintainer'))
    ac.db.commit()
    assert measure()==baseline
