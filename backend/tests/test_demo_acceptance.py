"""Demo guards, atomic idempotent fixtures and anonymous application acceptance."""
import json
import os
import subprocess
import sys
from pathlib import Path
from uuid import uuid4
import pytest
from sqlalchemy import create_engine, text, select, func
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient
from app.acceptance.demo import local_database, seed, QUESTIONS, identifier


@pytest.mark.parametrize('change',[
    {'APP_ENV':'production'}, {'OPENDEV_DEMO':''}, {'LLM_ENABLED':'true'},
    {'CHECKOUT_ENABLED':'true'}, {'RECEIPT_PROCESSING_ENABLED':'true'},
    {'DATABASE_URL':'postgresql+psycopg://u@production.invalid/opendev_test_demo_x'},
    {'DATABASE_URL':'postgresql+psycopg://u@localhost/opendev_production'},
    {'DATABASE_URL':'postgresql+psycopg://u@localhost/opendev_test_demo_x?host=production.invalid'},
    {'DATABASE_URL':'postgresql+psycopg://u@localhost/opendev_test_demo_x?options=-csearch_path=public%20-csession_preload_libraries=bad'},
])
def test_demo_target_guards(monkeypatch,change):
    for k,v in dict(APP_ENV='testing',OPENDEV_DEMO='synthetic-local',CHECKOUT_ENABLED='false',RECEIPT_PROCESSING_ENABLED='false',LLM_ENABLED='false',DATABASE_URL='postgresql+psycopg://u@localhost/opendev_test_demo_x').items():monkeypatch.setenv(k,v)
    for k,v in change.items():monkeypatch.setenv(k,v)
    with pytest.raises(ValueError):local_database()


@pytest.fixture
def demo():
    url=os.getenv('TEST_DATABASE_URL')
    if not url:pytest.skip('isolated PostgreSQL required')
    parsed=make_url(url)
    assert parsed.host in ('localhost','127.0.0.1') and parsed.database.startswith('opendev_test_')
    schema='demo_'+uuid4().hex
    admin=create_engine(url)
    with admin.begin() as connection:connection.execute(text(f'CREATE SCHEMA {schema}'))
    scoped=parsed.update_query_dict({'options':'-csearch_path='+schema}).render_as_string(hide_password=False)
    env=dict(os.environ,DATABASE_URL=scoped,APP_ENV='testing')
    subprocess.run([sys.executable,'-m','alembic','upgrade','head'],cwd=Path(__file__).parents[1],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,check=True)
    engine=create_engine(scoped)
    try:yield engine
    finally:
        engine.dispose()
        with admin.begin() as connection:connection.execute(text(f'DROP SCHEMA {schema} CASCADE'))
        admin.dispose()


def test_demo_seed_is_idempotent_and_does_not_overwrite(demo):
    from app.models.project import Project
    from app.models.funding import Contribution,RefundRecord
    first=seed(demo);again=seed(demo)
    assert first==again
    with Session(demo) as db:
        assert db.scalar(select(func.count()).select_from(Contribution))==4
        assert db.scalar(select(func.count()).select_from(RefundRecord))==1
        row=db.get(Project,first['project_id']);row.title='Existing user change';db.commit()
    with pytest.raises(ValueError):seed(demo)
    with Session(demo) as db:assert db.get(Project,first['project_id']).title=='Existing user change'


def test_demo_refuses_unrelated_records(demo):
    from app.models.user import User
    with Session(demo) as db:db.add(User(username='existing',github_id=42));db.commit()
    with pytest.raises(ValueError):seed(demo)
    with Session(demo) as db:assert db.scalar(select(func.count()).select_from(User))==1


def test_local_demo_public_acceptance(demo,monkeypatch):
    from app.main import app
    from app.core.database import get_db
    from app.core.config import settings
    from app.services import analytics_exports
    from app.agent import limits
    info=seed(demo)
    def session():
        with Session(demo) as db:yield db
    monkeypatch.setattr(settings,'LLM_ENABLED',False)
    monkeypatch.setattr(settings,'CHECKOUT_ENABLED',False)
    monkeypatch.setattr(settings,'RECEIPT_PROCESSING_ENABLED',False)
    monkeypatch.setattr(limits,'limiter',limits.RateLimiter())
    overrides=app.dependency_overrides.copy()
    assert not overrides,'Demo acceptance must use real authorization dependencies'
    app.dependency_overrides[get_db]=session
    analytics_exports._peers.clear()
    try:
        with TestClient(app) as client:
            pid=info['project_id'];private=info['private_project_id']
            assert client.get('/api/auth/me').status_code==401
            assert client.get(f'/api/projects/{private}').status_code==404
            for path in (f'/api/projects/{pid}',f'/api/projects/{pid}/transparency',f'/api/projects/{pid}/roadmap',f'/api/projects/{pid}/github/activity',f'/api/projects/{pid}/progress-summary',f'/api/maintainers/{info["owner_id"]}/credibility',f'/api/projects/{pid}/analytics/overview',f'/api/projects/{pid}/ledger/{info["expense_id"]}'):
                r=client.get(path);assert r.status_code==200,(path,r.text)
                assert 'DEMO_PRIVATE_' not in r.text
            overview=client.get(f'/api/projects/{pid}/analytics/overview').json()
            assert overview['financial']['net_recorded_funding_cents']==95000
            assert overview['financial']['published_reported_spending_cents']==65000
            assert overview['financial']['funding_minus_reported_expenditure_cents']==30000
            assert overview['financial']['exact_refund_total_cents'] is None
            assert client.get(f'/api/projects/{pid}/transparency').json()['public_unresolved_discrepancy_count']==1
            csv=client.get(f'/api/projects/{pid}/analytics/export/expenses');assert csv.status_code==200
            assert '35000' in csv.text and 'DEMO_PRIVATE_' not in csv.text
            results=[]
            for key,question in QUESTIONS:
                r=client.post(f'/api/projects/{pid}/agent/query',json={'project_id':pid,'question':question,'mode':'llm'})
                assert r.status_code==200,r.text
                value=r.json()
                assert value['execution_mode']=='deterministic' and value['citations']
                assert 'DEMO_PRIVATE_' not in r.text
                results.append({'key':key,'question':question,'answer':value['answer'],'answer_status':value['answer_status'],'actual_mode':value['execution_mode'],'citation_count':len(value['citations'])})
            assert results[0]['answer_status']=='answered' and '95000' in results[0]['answer']
            docs=client.get(f'/api/expenses/{info["expense_id"]}/documents')
            assert docs.status_code==200 and len(docs.json())==1 and 'DEMO_PRIVATE_' not in docs.text
            assert client.get(f'/api/documents/{identifier("original")}/download').status_code==404
            assert client.get(f'/api/projects/{private}/analytics/overview').status_code==404
            if os.getenv('PHASE7_DEMO_RESULTS'):
                Path(os.environ['PHASE7_DEMO_RESULTS']).write_text(json.dumps({'scope':info['scope'],'questions':results},indent=2)+'\n')
    finally:
        app.dependency_overrides.clear();app.dependency_overrides.update(overrides);analytics_exports._peers.clear()
