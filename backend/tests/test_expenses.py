"""Expense API and financial accounting integration tests; isolated PostgreSQL only."""
from uuid import uuid4

import pytest
from sqlalchemy import event, select, func
from sqlalchemy.exc import IntegrityError

from app.main import app
from app.core.auth import get_current_user
from app.models.expense import Expense
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.reward_tier import RewardTier
from app.models.budget_allocation import BudgetAllocation
from app.models.funding import Contribution
from app.schemas.expense import ExpenseCreate
from app.services import expenses
from test_projects import ctx


@pytest.fixture
def expense_ctx(ctx):
    client, db, project, users, identity = ctx
    project.status = 'active'
    db.commit()
    return ctx


def payload(**changes):
    return dict(category='Development', amount_cents=1000, currency='USD', vendor='Hosting provider', description='Reported development hosting cost', expense_date='2026-10-31', **changes)


def create(context, **changes):
    client, _, project, _, _ = context
    data = payload(); data.update(changes)
    return client.post(f'/api/projects/{project.id}/expenses', json=data)


def publish(context, **changes):
    client, *_ = context
    result = create(context, **changes)
    assert result.status_code == 201, result.text
    return client.post(f"/api/expenses/{result.json()['id']}/publish")


@pytest.mark.parametrize('actor', [0, 1])
def test_owner_and_maintainer_can_create_and_edit(expense_ctx, actor):
    client, db, project, users, identity = expense_ctx
    identity[0] = users[actor]
    result = create(expense_ctx)
    assert result.status_code == 201
    data = result.json()
    assert data['submitted_by_user_id'] == users[actor].id
    assert data['publication_status'] == 'draft'
    assert data['evidence_status'] == 'unverified'
    edited = client.patch(f"/api/expenses/{data['id']}", json={'amount_cents': 2000})
    assert edited.status_code == 200
    assert edited.json()['amount_cents'] == 2000
    assert edited.json()['updated_at'] >= data['updated_at']


@pytest.mark.parametrize('actor', [2, 3])
def test_collaborator_and_outsider_cannot_write(expense_ctx, actor):
    client, db, p, users, identity = expense_ctx
    eid = create(expense_ctx).json()['id']
    identity[0] = users[actor]
    assert create(expense_ctx).status_code == 403
    assert client.patch(f'/api/expenses/{eid}', json={'vendor':'Forged'}).status_code == 403
    assert client.post(f'/api/expenses/{eid}/publish').status_code == 403
    assert client.get(f'/api/expenses/{eid}').status_code == 404


def test_anonymous_writes_and_csrf(expense_ctx):
    client, db, p, users, identity = expense_ctx
    eid = create(expense_ctx).json()['id']
    for origin in ['', 'https://evil.example']:
        assert client.post(f'/api/projects/{p.id}/expenses',json=payload(),headers={'Origin':origin}).status_code == 403
        assert client.patch(f'/api/expenses/{eid}',json={'vendor':'Changed'},headers={'Origin':origin}).status_code == 403
        assert client.post(f'/api/expenses/{eid}/publish',headers={'Origin':origin}).status_code == 403
    app.dependency_overrides.pop(get_current_user)
    assert create(expense_ctx).status_code == 401
    assert client.patch(f'/api/expenses/{eid}',json={'vendor':'Changed'}).status_code == 401
    assert client.post(f'/api/expenses/{eid}/publish').status_code == 401


@pytest.mark.parametrize('field,value', [('amount_cents',0),('amount_cents',-5),('amount_cents',1.5),('amount_cents',True),('amount_cents','100'),('amount_cents',9223372036854775808),('currency','EUR'),('category',' '),('vendor',' '),('description',' '),('expense_date','invalid'),('project_id',1),('submitted_by_user_id',1),('evidence_status','verified'),('publication_status','published')])
def test_invalid_and_server_controlled_fields(expense_ctx, field, value):
    assert create(expense_ctx, **{field:value}).status_code == 422


def test_cross_project_access_and_no_reassignment(expense_ctx):
    client, db, p, users, identity = expense_ctx
    eid = create(expense_ctx).json()['id']
    other = Project(owner_id=users[3].id,github_repo_id=999,github_repo_url='https://github.com/other/repo',title='Other project',description='Another project description',funding_goal_cents=10000,currency='USD',status='active')
    db.add(other); db.flush()
    db.add(ProjectMember(project_id=other.id,user_id=users[2].id,role='maintainer')); db.commit()
    identity[0] = users[2]
    assert client.post(f'/api/projects/{other.id}/expenses',json=payload()).status_code == 201
    assert client.patch(f'/api/expenses/{eid}',json={'amount_cents':1}).status_code == 403
    assert client.post(f'/api/expenses/{eid}/publish').status_code == 403
    assert client.get(f'/api/projects/{p.id}/expenses?include_drafts=true').status_code == 403
    identity[0] = users[0]
    assert client.patch(f'/api/expenses/{eid}',json={'project_id':other.id}).status_code == 422
    assert client.get(f'/api/projects/{other.id}/expenses?include_drafts=true').status_code == 403


def test_publication_visibility_and_immutability(expense_ctx):
    client, db, p, users, identity = expense_ctx
    eid = create(expense_ctx).json()['id']
    assert client.get(f'/api/projects/{p.id}/expenses').json() == []
    assert len(client.get(f'/api/projects/{p.id}/expenses?include_drafts=true').json()) == 1
    identity[0] = None
    assert client.get(f'/api/expenses/{eid}').status_code == 404
    assert client.get(f'/api/projects/{p.id}/financial-summary').json()['reported_spending_cents'] == 0
    identity[0] = users[0]
    for _ in range(2):
        assert client.post(f'/api/expenses/{eid}/publish').status_code == 200
    assert client.patch(f'/api/expenses/{eid}',json={'vendor':'Rewrite'}).status_code == 409
    identity[0] = None
    assert client.get(f'/api/expenses/{eid}').json()['publication_status'] == 'published'
    assert len(client.get(f'/api/projects/{p.id}/expenses').json()) == 1


def test_financial_aggregation_and_refund_policy(expense_ctx):
    client, db, p, users, identity = expense_ctx
    publish(expense_ctx, category=' development ', amount_cents=12000)
    publish(expense_ctx, category='Equipment', amount_cents=2000)
    create(expense_ctx,amount_cents=999999)
    tier=RewardTier(project_id=p.id,name='Backer',description='Thanks',price_cents=500,currency='USD',benefits=[{'title':'Thanks'}]);db.add(tier);db.flush()
    for status, amount, capture_id, currency in [('completed',20000,'CAP1','USD'),('completed',500,None,'USD'),('pending',3000,'PENDING','USD'),('denied',4000,'DENIED','USD'),('refunded',5000,'REFUND','USD'),('reversed',6000,'REVERSE','USD'),('cancelled',7000,None,'USD'),('completed',200,'FOREIGN','EUR')]:
        db.add(Contribution(id=str(uuid4()),user_id=users[0].id,project_id=p.id,tier_id=tier.id,checkout_key=str(uuid4()),amount_cents=amount,currency=currency,reward_snapshot={},status=status,capture_id=capture_id,capture_key=str(uuid4())))
    other=Project(owner_id=users[0].id,github_repo_id=12345,github_repo_url='https://github.com/a/b',title='Other',description='Other project description',funding_goal_cents=1,currency='USD',status='active');db.add(other);db.flush()
    db.add(Expense(project_id=other.id,submitted_by_user_id=users[0].id,category='Development',amount_cents=555,currency='USD',vendor='Other',description='Other expense',expense_date=__import__('datetime').date(2026,10,31),publication_status='published'))
    db.commit()
    identity[0]=None
    data=client.get(f'/api/projects/{p.id}/financial-summary').json()
    assert data['completed_funding_cents']==20000
    assert data['excluded_refunded_or_reversed_cents']==11000
    assert data['excluded_other_status_cents']==7000
    assert data['excluded_currency_mismatch_count']==1
    assert data['reported_spending_cents']==14000
    assert data['independently_verified_spending_cents']==0
    assert data['allocated_budget_cents']==10000
    assert data['budget_remaining_cents']==-4000
    assert data['funding_less_reported_spending_cents']==6000
    assert data['expense_count']==2
    categories={c['category']:c for c in data['categories']}
    assert categories['development']['overspend_cents']==2000
    assert categories['equipment']['allocated_cents']==0
    assert categories['equipment']['budget_remaining_cents']==-2000


def test_empty_summary_and_paused_completed_project_visibility(expense_ctx):
    client, db, p, users, identity = expense_ctx
    for status in ['active','paused','completed']:
        p.status=status;db.commit();identity[0]=None
        data=client.get(f'/api/projects/{p.id}/financial-summary').json()
        assert data['reported_spending_cents']==data['completed_funding_cents']==0
    p.status='draft';db.commit()
    assert client.get(f'/api/projects/{p.id}/financial-summary').status_code==404
    identity[0]=users[0]
    assert create(expense_ctx).status_code==409


def test_transaction_rollback(expense_ctx):
    client, db, p, users, identity = expense_ctx
    before=db.scalar(select(func.count()).select_from(Expense))
    def failure(session):
        # Flush the INSERT, then fail the transaction before commit.
        session.flush()
        raise RuntimeError('simulated write failure')
    event.listen(db,'before_commit',failure)
    try:
        with pytest.raises(RuntimeError,match='simulated'):
            expenses.create(db,p.id,users[0],ExpenseCreate(**payload()))
    finally:
        event.remove(db,'before_commit',failure)
    assert db.scalar(select(func.count()).select_from(Expense))==before
    assert create(expense_ctx).status_code==201


@pytest.mark.parametrize('invalid', [{'amount_cents':0},{'currency':'EUR'},{'evidence_status':'verified'},{'publication_status':'invalid'},{'project_id':9223372036854775807},{'submitted_by_user_id':9223372036854775807}])
def test_database_constraints(expense_ctx, invalid):
    client, db, p, users, identity = expense_ctx
    data=ExpenseCreate(**payload()).model_dump()
    data.update(project_id=p.id,submitted_by_user_id=users[0].id)
    data.update(invalid)
    with pytest.raises(IntegrityError):
        with db.begin_nested():
            db.add(Expense(**data));db.flush()


@pytest.mark.parametrize('changes', [{'amount_cents':0}, {'amount_cents':1.5}, {'vendor':None}, {'currency':'EUR'}, {'evidence_status':'verified'}, {'publication_status':'published'}, {'submitted_by_user_id':999}])
def test_invalid_draft_edit_preserves_original(expense_ctx, changes):
    client, db, p, users, identity = expense_ctx
    original=create(expense_ctx).json()
    assert client.patch(f"/api/expenses/{original['id']}",json=changes).status_code == 422
    current=client.get(f"/api/expenses/{original['id']}").json()
    assert current==original


def test_pagination_missing_records_and_invalid_ids(expense_ctx):
    client, db, p, users, identity = expense_ctx
    first=publish(expense_ctx, expense_date='2026-10-01').json()
    second=publish(expense_ctx, expense_date='2026-10-02').json()
    assert client.get(f'/api/projects/{p.id}/expenses?limit=1').json()[0]['id']==second['id']
    assert client.get(f'/api/projects/{p.id}/expenses?limit=1&offset=1').json()[0]['id']==first['id']
    assert client.get(f'/api/projects/{p.id}/expenses?limit=101').status_code==422
    assert client.get('/api/expenses/9223372036854775808').status_code==422
    assert client.get('/api/expenses/9223372036854775807').status_code==404
    assert client.get('/api/projects/9223372036854775807/financial-summary').status_code==404
