"""Integration tests require an explicitly supplied isolated TEST_DATABASE_URL."""
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from app.main import app
from app.core.database import get_db
from app.core.auth import get_current_user, get_optional_user
from app.core.config import settings
from app.models.user import User
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.budget_allocation import BudgetAllocation
from app.services import project_management
from app.routers import projects

@pytest.fixture()
def ctx(monkeypatch):
    url = os.getenv('TEST_DATABASE_URL')
    if not url:
        pytest.skip('Set TEST_DATABASE_URL to a migrated isolated test database')
    from sqlalchemy.engine import make_url
    if make_url(url).host not in ('127.0.0.1', 'localhost', None) or not make_url(url).database.startswith('opendev_test_'):
        pytest.fail('Integration tests require a local opendev_test_* database')
    engine = create_engine(url)
    with engine.connect() as conn:
        transaction = conn.begin()
        db = Session(bind=conn, join_transaction_mode='create_savepoint')
        users = [User(username=n, github_id=i + 100) for i, n in enumerate(['owner', 'maintainer', 'collaborator', 'outsider'])]
        db.add_all(users); db.flush()
        project = Project(owner_id=users[0].id, github_repo_id=42, github_repo_url='https://github.com/owner/repo', title='Test project', description='A detailed project description', funding_goal_cents=10000, currency='USD', status='draft')
        db.add(project); db.flush()
        db.add_all([ProjectMember(project_id=project.id, user_id=users[i].id, role=role) for i, role in [(1,'maintainer'),(2,'collaborator')]])
        db.add(BudgetAllocation(project_id=project.id, category='Development', allocated_cents=10000)); db.commit()
        identity = [users[0]]
        app.dependency_overrides[get_db] = lambda: db
        app.dependency_overrides[get_current_user] = lambda: identity[0]
        app.dependency_overrides[get_optional_user] = lambda: identity[0]
        async def verify(repo_name, github_user_id):
            assert repo_name == 'owner/repo'
            assert github_user_id == users[0].github_id
            return {'id': 42, 'url': 'https://github.com/owner/repo'}
        monkeypatch.setattr(project_management, 'verify_repository_ownership', verify)
        monkeypatch.setattr(projects, 'verify_repository_ownership', verify)
        with TestClient(app, headers={'Origin': settings.FRONTEND_URL}) as client:
            yield client, db, project, users, identity
        app.dependency_overrides.clear()
        db.close(); transaction.rollback()
    engine.dispose()


def reward(**changes):
    return dict(name='Early Access', description='Get beta access', price_cents=500, currency='USD', benefits=[{'title':'Beta access','description':'Private preview'}], **changes)


def test_publish_and_public_detail(ctx):
    client, db, p, users, identity = ctx
    assert client.post(f'/api/projects/{p.id}/publish').status_code == 200
    identity[0] = None
    result = client.get(f'/api/projects/{p.id}')
    assert result.status_code == 200
    assert result.json()['budget'][0]['allocated_cents'] == 10000
    assert result.json()['maintainers'][0]['username'] in ('owner','maintainer')
    assert not result.json()['can_manage']
    assert p.id in [item['id'] for item in client.get('/api/projects').json()]

@pytest.mark.parametrize('actor', [2,3])
def test_unauthorized_project_and_reward_edits(ctx, actor):
    client, db, p, users, identity = ctx
    p.status = 'active'; db.commit(); identity[0] = users[actor]
    assert client.patch(f'/api/projects/{p.id}', json={'title':'Changed title'}).status_code == 403
    assert client.post(f'/api/projects/{p.id}/rewards', json=reward()).status_code == 403
    assert client.post(f'/api/projects/{p.id}/publish').status_code == 403


def test_maintainer_edit_and_my_projects(ctx):
    client, db, p, users, identity = ctx
    identity[0] = users[1]
    assert client.patch(f'/api/projects/{p.id}', json={'title':'New project title'}).status_code == 200
    assert client.post(f'/api/projects/{p.id}/rewards', json=reward()).status_code == 201
    assert client.get('/api/me/projects').json()[0]['id'] == p.id
    identity[0] = users[2]
    assert client.get('/api/me/projects').json() == []

@pytest.mark.parametrize('field,value', [('price_cents',0),('price_cents',-1),('price_cents',1.5),('currency','EUR'),('quantity_limit',0),('name',' '),('benefits',[])])
def test_invalid_rewards(ctx, field, value):
    client, _, p, _, _ = ctx
    data = reward(); data[field] = value
    assert client.post(f'/api/projects/{p.id}/rewards', json=data).status_code == 422


def test_duplicate_rewards_and_patch(ctx):
    client, db, p, _, _ = ctx
    first = client.post(f'/api/projects/{p.id}/rewards', json=reward()).json()
    data = reward(); data['name'] = ' early access '
    assert client.post(f'/api/projects/{p.id}/rewards', json=data).status_code == 409
    data['name'] = 'Sponsor'
    second = client.post(f'/api/projects/{p.id}/rewards', json=data).json()
    assert client.patch(f"/api/projects/{p.id}/rewards/{second['id']}", json={'name':'EARLY ACCESS'}).status_code == 409
    assert client.patch(f"/api/projects/{p.id}/rewards/{first['id']}", json={'quantity_limit':None,'active':False}).status_code == 200
    assert client.patch(f"/api/projects/{p.id}/rewards/{first['id']}", json={'name':None}).status_code == 422
    assert client.patch(f'/api/projects/{p.id}/rewards/999999', json={'name':'Missing'}).status_code == 404


def test_budget_validation_and_draft_edit(ctx):
    client, db, p, _, _ = ctx
    assert client.patch(f'/api/projects/{p.id}', json={'funding_goal_cents':20000}).status_code == 422
    assert client.patch(f'/api/projects/{p.id}', json={'status':'active'}).status_code == 422
    assert client.patch(f'/api/projects/{p.id}', json={'budget':[{'category':'Work','allocated_cents':5000},{'category':' work ','allocated_cents':5000}]}).status_code == 422
    assert client.patch(f'/api/projects/{p.id}', json={'funding_goal_cents':20000,'budget':[{'category':'Development','allocated_cents':20000}]}).status_code == 200
    db.scalar(select(BudgetAllocation).where(BudgetAllocation.project_id == p.id)).allocated_cents = 1; db.commit()
    assert client.post(f'/api/projects/{p.id}/publish').status_code == 422


def test_visibility(ctx):
    client, db, p, users, identity = ctx
    assert client.get(f'/api/projects/{p.id}').status_code == 200
    identity[0] = None
    assert client.get(f'/api/projects/{p.id}').status_code == 404
    assert client.get(f'/api/projects/{p.id}/rewards').status_code == 404
    assert client.get('/api/projects').json() == []
    identity[0] = users[0]
    tier = client.post(f'/api/projects/{p.id}/rewards', json=reward()).json()
    client.patch(f"/api/projects/{p.id}/rewards/{tier['id']}",json={'active':False})
    client.post(f'/api/projects/{p.id}/publish')
    identity[0] = None
    assert client.get(f'/api/projects/{p.id}/rewards').json() == []


def test_repository_revalidated(ctx, monkeypatch):
    client, db, p, _, _ = ctx
    async def changed(*args): return {'id':99}
    monkeypatch.setattr(project_management, 'verify_repository_ownership', changed)
    assert client.post(f'/api/projects/{p.id}/publish').status_code == 422
    assert db.get(Project, p.id).status == 'draft'


def test_csrf_and_immutable_fields(ctx):
    client, _, p, _, _ = ctx
    assert client.patch(f'/api/projects/{p.id}',json={'title':'New title'},headers={'Origin':'https://evil.example'}).status_code == 403
    assert client.post(f'/api/projects/{p.id}/publish',headers={'Origin':'https://evil.example'}).status_code == 403
    assert client.post(f'/api/projects/{p.id}/rewards',json=reward(),headers={'Origin':'https://evil.example'}).status_code == 403
    assert client.patch(f'/api/projects/{p.id}',json={'owner_id':42}).status_code == 422


def test_cookie_session_and_anonymous_writes(ctx):
    from app.services.session_service import create_session, SESSION_COOKIE
    client, db, p, users, _ = ctx
    app.dependency_overrides.pop(get_current_user)
    app.dependency_overrides.pop(get_optional_user)
    assert client.get('/api/me/projects').status_code == 401
    assert client.patch(f'/api/projects/{p.id}',json={'title':'Cannot edit'}).status_code == 401
    assert client.get(f'/api/projects/{p.id}').status_code == 404
    token = create_session(db, users[1].id)
    client.cookies.set(SESSION_COOKIE, token)
    assert client.get(f'/api/projects/{p.id}').json()['can_manage']
    assert client.patch(f'/api/projects/{p.id}',json={'title':'Maintainer edits'}).status_code == 200


def test_cross_project_reward_and_active_project_edit(ctx):
    from app.models.reward_tier import RewardTier
    client, db, p, users, _ = ctx
    other = Project(owner_id=users[0].id, github_repo_id=99, github_repo_url='https://github.com/owner/other', title='Other project',description='Another project description',funding_goal_cents=100, currency='USD',status='draft')
    db.add(other); db.flush()
    tier = RewardTier(project_id=other.id, **reward()); db.add(tier); db.commit()
    assert client.patch(f'/api/projects/{p.id}/rewards/{tier.id}', json={'price_cents':200}).status_code == 404
    assert client.post(f'/api/projects/{p.id}/publish').status_code == 200
    assert client.patch(f'/api/projects/{p.id}',json={'funding_goal_cents':20000}).status_code == 409
    assert client.post(f'/api/projects/{p.id}/publish').status_code == 409
