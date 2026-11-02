"""Reconciliation and append-only review integration tests in isolated schemas."""
import hashlib
import os
from pathlib import Path
import subprocess
from uuid import uuid4
from datetime import date, datetime, timezone, timedelta
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select, text, func, update
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session
from sqlalchemy.exc import DBAPIError, IntegrityError

from app.main import app
from app.core.auth import get_current_user,get_optional_user
from app.core.database import get_db
from app.core.config import settings
from app.models.user import User
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.budget_allocation import BudgetAllocation
from app.models.expense import Expense
from app.models.expense_document import ExpenseDocument
from app.models.funding import Contribution,WebhookEvent
from app.models.reward_tier import RewardTier
from app.models.receipt_extraction import ReceiptExtraction
from app.models.finding_review import FindingReview
from app.services import accountability
from app.services.receipt import pipeline
from app.services.receipt.parser import parse

TEXT='Vendor: Acme Hosting\nInvoice No: INV-1\nDate: 2026-10-31\nCurrency: USD\nGrand Total: USD 12.34'


@pytest.fixture
def ac():
    url=os.getenv('TEST_DATABASE_URL')
    if not url:pytest.skip('isolated PostgreSQL required')
    parsed=make_url(url)
    assert parsed.host in ('localhost','127.0.0.1',None) and parsed.database.startswith('opendev_test_')
    schema='accountability_'+uuid4().hex
    admin=create_engine(url)
    with admin.begin() as connection:connection.execute(text(f'CREATE SCHEMA {schema}'))
    scoped=parsed.update_query_dict({'options':'-csearch_path='+schema}).render_as_string(hide_password=False)
    env=dict(os.environ,DATABASE_URL=scoped,APP_ENV='testing')
    subprocess.run([str(Path(__import__('sys').executable).with_name('alembic')),'upgrade','head'],cwd=Path(__file__).parents[1],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,check=True)
    engine=create_engine(scoped)
    db=Session(engine,expire_on_commit=False)
    users=[User(username=name,github_id=i+100) for i,name in enumerate(['owner','maintainer','collaborator','other-owner'])]
    db.add_all(users);db.flush()
    p=Project(owner_id=users[0].id,github_repo_id=1,github_repo_url='https://github.com/test/project',title='Synthetic project',description='Synthetic fixture',funding_goal_cents=10000,currency='USD',status='active')
    other=Project(owner_id=users[3].id,github_repo_id=2,github_repo_url='https://github.com/other/project',title='Other',description='Other fixture',funding_goal_cents=10000,currency='USD',status='active')
    db.add_all([p,other]);db.flush()
    db.add_all([ProjectMember(project_id=p.id,user_id=users[1].id,role='maintainer'),ProjectMember(project_id=p.id,user_id=users[2].id,role='collaborator'),BudgetAllocation(project_id=p.id,category='Development',allocated_cents=10000)])
    e=Expense(project_id=p.id,submitted_by_user_id=users[0].id,category='Development',amount_cents=1000,currency='USD',vendor='Acme Hosting',description='Synthetic expense',expense_date=date(2026,10,31),publication_status='published')
    db.add(e);db.flush()
    tier=RewardTier(project_id=p.id,name='Synthetic',description='Synthetic',price_cents=1000,currency='USD',benefits=[{'title':'Synthetic'}]);db.add(tier);db.commit()
    identity=[users[0]]
    def test_db():
        with Session(engine,expire_on_commit=False) as session:yield session
    app.dependency_overrides[get_db]=test_db
    app.dependency_overrides[get_current_user]=lambda:identity[0]
    app.dependency_overrides[get_optional_user]=lambda:identity[0]
    with TestClient(app,headers={'Origin':settings.FRONTEND_URL}) as client:
        yield SimpleNamespace(client=client,db=db,engine=engine,users=users,identity=identity,p=p,other=other,e=e,tier=tier)
    app.dependency_overrides.clear();db.close();engine.dispose();admin.dispose()
    # Retained isolated schema in disposable local DB; no destructive cleanup.


def contribution(ac,status='completed',amount=2000,capture=True):
    row=Contribution(id=str(uuid4()),user_id=ac.users[0].id,project_id=ac.p.id,tier_id=ac.tier.id,checkout_key=str(uuid4()),amount_cents=amount,currency='USD',reward_snapshot={},status=status,capture_id='CAP'+uuid4().hex if capture else None,capture_key=str(uuid4()))
    ac.db.add(row);ac.db.commit();return row


def receipt(ac,total='12.34',quality=100,version=None,expense=None,code='completed'):
    doc=ExpenseDocument(id=str(uuid4()),expense_id=(expense or ac.e).id,uploaded_by=ac.users[0].id,storage_key='receipts/'+str(uuid4()),original_filename='private.pdf',detected_mime_type='application/pdf',file_size_bytes=5,sha256_hash=hashlib.sha256(uuid4().bytes).hexdigest())
    ac.db.add(doc);ac.db.flush()
    record=ReceiptExtraction(id=str(uuid4()),expense_document_id=doc.id,extraction_version=version or pipeline.VERSION,extraction_status=code,
                             extracted_json=parse([{'text':line,'page':1,'quality':quality} for line in TEXT.replace('12.34',total).splitlines()],'pdf_text',1).model_dump(mode='json') if code=='completed' else None,processing_error_code='SYNTHETIC_TIMEOUT' if code=='failed' else None)
    ac.db.add(record);ac.db.commit();return doc,record


def verification(ac):
    result=ac.client.get(f'/api/expenses/{ac.e.id}/verification');assert result.status_code==200,result.text;return result.json()


def decision(ac,finding,action='mark_reviewed',**changes):
    data=dict(request_key=str(uuid4()),action=action,reason='Synthetic private review explanation.');data.update(changes)
    return ac.client.post('/api/extraction-findings/'+finding['id']+'/review',json=data)


def test_funding_and_budget_reconciliation(ac):
    contribution(ac,'completed',20000);contribution(ac,'refunded',3000);contribution(ac,'reversed',4000)
    for status in ['pending','denied','failed','cancelled']:contribution(ac,status,9000)
    contribution(ac,'completed',9999,capture=False)
    ac.db.add(Expense(project_id=ac.p.id,submitted_by_user_id=ac.users[0].id,category=' development ',amount_cents=12000,currency='USD',vendor='Other',description='Synthetic',expense_date=date(2026,10,31),publication_status='published'));ac.db.commit()
    data=ac.client.get(f'/api/projects/{ac.p.id}/accountability').json()
    assert data['gross_completed_funding_cents']==27000
    assert data['refund_excluded_cents']==3000 and data['reversal_excluded_cents']==4000
    assert data['net_recorded_funding_cents']==20000
    assert data['published_reported_spending_cents']==13000
    assert data['funding_minus_reported_expenditure_cents']==7000
    assert data['exact_refund_total_cents'] is None
    assert data['budget_variance'][0]['overspend_cents']==3000
    assert ac.client.get(f'/api/projects/{ac.p.id}/budget-variance').json()['categories']==data['budget_variance']


def test_duplicate_capture_and_webhook_cannot_inflate(ac):
    c=contribution(ac)
    with pytest.raises(IntegrityError):
        with ac.db.begin_nested():
            ac.db.add(Contribution(id=str(uuid4()),user_id=c.user_id,project_id=c.project_id,tier_id=c.tier_id,checkout_key=str(uuid4()),amount_cents=c.amount_cents,currency=c.currency,reward_snapshot={},status='completed',capture_id=c.capture_id,capture_key=str(uuid4())));ac.db.flush()
    ac.db.add(WebhookEvent(id='EVENT1',event_type='PAYMENT.CAPTURE.COMPLETED'));ac.db.commit()
    with pytest.raises(IntegrityError):
        with ac.db.begin_nested():ac.db.add(WebhookEvent(id='EVENT1',event_type='PAYMENT.CAPTURE.COMPLETED'));ac.db.flush()
    assert ac.client.get(f'/api/projects/{ac.p.id}/accountability').json()['net_recorded_funding_cents']==2000


def test_multiple_receipts_versions_and_low_confidence(ac):
    doc,old=receipt(ac,version='old-version')
    # Current consistent extraction supersedes old mismatch, never adds another expense.
    current=ReceiptExtraction(id=str(uuid4()),expense_document_id=doc.id,extraction_version=pipeline.VERSION,extraction_status='completed',extracted_json=parse([{'text':line,'page':1,'quality':100} for line in TEXT.replace('12.34','10.00').splitlines()],'pdf_text',1).model_dump(mode='json'))
    ac.db.add(current);ac.db.commit()
    assert verification(ac)['classification']=='extraction_consistent'
    second,_=receipt(ac,total='13.00',quality=35)
    data=verification(ac)
    assert data['classification']=='discrepancy_detected'
    assert data['findings'][0]['severity']=='info'
    third,_=receipt(ac,total='13.00',quality=35)
    snapshot=ac.client.get(f'/api/projects/{ac.p.id}/accountability').json()
    assert snapshot['published_expense_count']==1 and snapshot['published_reported_spending_cents']==1000
    assert snapshot['expenses_with_documents_count']==1 and snapshot['expenses_with_documents_cents']==1000
    assert snapshot['unresolved_discrepancy_count']==1
    assert snapshot['independently_payment_matched_cents']==0


@pytest.mark.parametrize('actor',[0,1])
def test_review_is_audited_but_not_resolution(ac,actor):
    receipt(ac);ac.identity[0]=ac.users[actor]
    finding=verification(ac)['findings'][0]
    response=decision(ac,finding,'accept_field',field_name='total_cents')
    assert response.status_code==200,response.text
    data=verification(ac)
    assert data['findings'][0]['review_status']=='accepted' and data['findings'][0]['resolved'] is False
    assert 'human_reviewed' in data['evidence_states'] and 'discrepancy_detected' in data['evidence_states']
    assert data['unresolved_discrepancy_count']==1
    history=ac.client.get(f'/api/expenses/{ac.e.id}/review-history').json()
    assert history[0]['actor_id']==ac.users[actor].id and history[0]['outcome']=='unresolved'
    ac.db.refresh(ac.e);assert ac.e.amount_cents==1000 and ac.e.evidence_status=='unverified'


@pytest.mark.parametrize('actor',[2,3])
def test_cross_project_review_permissions(ac,actor):
    receipt(ac);finding=verification(ac)['findings'][0];ac.identity[0]=ac.users[actor]
    assert decision(ac,finding).status_code in (403,404)
    assert ac.client.get(f'/api/expenses/{ac.e.id}/review-history').status_code in (403,404)
    public=verification(ac)
    assert public['findings']==[] and public['unresolved_discrepancy_count'] is None


def test_review_reason_csrf_idempotency_and_forbidden_certification(ac):
    receipt(ac);finding=verification(ac)['findings'][0]
    data=dict(request_key=str(uuid4()),action='dispute_field',field_name='total_cents',reason='A detailed human dispute explanation.')
    path='/api/extraction-findings/'+finding['id']+'/review'
    assert ac.client.post(path,json={**data,'reason':''}).status_code==422
    assert ac.client.post(path,json=data,headers={'Origin':'https://evil.example'}).status_code==403
    assert ac.client.post(path,json={**data,'action':'independently_payment_matched'}).status_code==422
    first=ac.client.post(path,json=data);assert first.status_code==200,first.text
    assert ac.client.post(path,json=data).json()['id']==first.json()['id']
    assert ac.client.post(path,json={**data,'reason':'Different human explanation.'}).status_code==409
    assert ac.db.scalar(select(func.count()).select_from(FindingReview))==1


def test_append_only_database_audit(ac):
    receipt(ac);finding=verification(ac)['findings'][0];decision(ac,finding)
    for statement in [text('UPDATE finding_reviews SET reason = :reason'),text('DELETE FROM finding_reviews')]:
        with pytest.raises(DBAPIError):
            with ac.db.begin_nested():ac.db.execute(statement,{'reason':'Tampered review entry'})
    assert ac.db.scalar(select(func.count()).select_from(FindingReview))==1


def test_public_only_approved_evidence_and_published_expenses(ac):
    original,record=receipt(ac);finding=verification(ac)['findings'][0];decision(ac,finding)
    private_uuid=original.id
    ac.e.publication_status='draft';ac.db.commit();ac.identity[0]=None
    assert ac.client.get(f'/api/expenses/{ac.e.id}/verification').status_code==404
    assert ac.client.get(f'/api/projects/{ac.p.id}/accountability').json()['published_expense_count']==0
    ac.e.publication_status='published';ac.db.commit()
    public=verification(ac)
    assert public['supporting_document_count']==0 and public['approved_public_document_ids']==[]
    snapshot=ac.client.get(f'/api/projects/{ac.p.id}/accountability').json()
    assert snapshot['unresolved_discrepancy_count'] is None
    assert private_uuid not in str(snapshot) and 'Synthetic private review' not in str(public)
    redacted=ExpenseDocument(id=str(uuid4()),expense_id=ac.e.id,uploaded_by=ac.users[0].id,storage_key='receipts/'+str(uuid4()),original_filename='public.png',detected_mime_type='image/png',file_size_bytes=5,sha256_hash=hashlib.sha256(b'redacted').hexdigest(),redacted_from_id=original.id,publication_status='published',approved_by=ac.users[0].id,approved_at=datetime.now(timezone.utc));ac.db.add(redacted);ac.db.commit()
    public=verification(ac)
    assert public['approved_public_document_ids']==[redacted.id] and public['supporting_document_count']==1
    assert public['findings']==[] and 'human_reviewed' not in public['evidence_states']
    ac.p.status='draft';ac.db.commit()
    assert ac.client.get(f'/api/projects/{ac.p.id}/accountability').status_code==404


def test_reconciliation_resolution_and_stale_findings(ac):
    receipt(ac);finding=verification(ac)['findings'][0];decision(ac,finding)
    ac.e.amount_cents=1100;ac.db.commit()
    assert decision(ac,finding).status_code==409
    assert ac.client.get(f'/api/expenses/{ac.e.id}/review-history').json()[0]['outcome']=='unresolved'
    ac.e.amount_cents=1234;ac.db.commit()
    assert verification(ac)['unresolved_discrepancy_count']==0
    assert ac.client.get(f'/api/expenses/{ac.e.id}/review-history').json()[0]['outcome']=='no_longer_detected'


def test_review_retry_reuses_existing_pipeline(ac,monkeypatch):
    doc,record=receipt(ac,code='failed')
    finding=verification(ac)['findings'][0];called=[]
    def retried(db,document,user,retry):called.append((document.id,retry));return db.get(ReceiptExtraction,record.id)
    monkeypatch.setattr(pipeline,'process',retried)
    response=decision(ac,finding,'request_retry')
    assert response.status_code==200,response.text
    assert called==[(doc.id,True)]
    assert ac.db.scalar(select(func.count()).select_from(FindingReview))==1


def test_repeatable_snapshot_during_concurrent_updates(ac):
    c=contribution(ac,'completed',5000)
    with accountability.read_snapshot(ac.db) as reader:
        project=reader.get(Project,ac.p.id)
        reader.scalar(select(func.count()).select_from(Contribution))
        with Session(ac.engine) as writer:
            contribution_row=writer.get(Contribution,c.id);contribution_row.status='refunded'
            expense=writer.get(Expense,ac.e.id);expense.amount_cents=2000;writer.commit()
        snapshot=accountability.snapshot(reader,project,SimpleNamespace(id=ac.users[0].id))
        assert snapshot['net_recorded_funding_cents']==5000 and snapshot['published_reported_spending_cents']==1000
    latest=ac.client.get(f'/api/projects/{ac.p.id}/accountability').json()
    assert latest['net_recorded_funding_cents']==0 and latest['published_reported_spending_cents']==2000


def test_readonly_verification_never_changes_ledger(ac):
    c=contribution(ac);doc,record=receipt(ac)
    before=ac.db.get(Contribution,c.id).amount_cents
    for path in [f'/api/projects/{ac.p.id}/accountability',f'/api/projects/{ac.p.id}/budget-variance',f'/api/expenses/{ac.e.id}/verification']:
        assert ac.client.get(path).status_code==200
    ac.db.refresh(ac.e);ac.db.refresh(c);ac.db.refresh(record)
    assert ac.e.evidence_status=='unverified' and ac.e.amount_cents==1000
    assert c.amount_cents==before and c.status=='completed'
    assert record.extracted_json['total_cents']['value']==1234


def test_concurrent_same_key_reviews_append_once(ac):
    from concurrent.futures import ThreadPoolExecutor
    receipt(ac);finding=verification(ac)['findings'][0]
    body=dict(request_key=str(uuid4()),action='mark_reviewed',reason='Two requests for the same human decision.')
    path='/api/extraction-findings/'+finding['id']+'/review'
    with ThreadPoolExecutor(max_workers=2) as pool:
        responses=list(pool.map(lambda _:ac.client.post(path,json=body),range(2)))
    assert all(r.status_code==200 for r in responses),[r.text for r in responses]
    assert len({r.json()['id'] for r in responses})==1
    assert ac.db.scalar(select(func.count()).select_from(FindingReview))==1
    assert verification(ac)['unresolved_discrepancy_count']==1


def test_unknown_new_version_does_not_resolve_old_mismatch(ac,monkeypatch):
    doc,record=receipt(ac);finding=verification(ac)['findings'][0];decision(ac,finding)
    receipt_json=parse([{'text':line,'page':1,'quality':100} for line in TEXT.splitlines() if not line.startswith('Grand Total')],'pdf_text',1).model_dump(mode='json')
    ac.db.add(ReceiptExtraction(id=str(uuid4()),expense_document_id=doc.id,extraction_version='local-rules-v2',extraction_status='completed',extracted_json=receipt_json));ac.db.commit()
    monkeypatch.setattr(pipeline,'VERSION','local-rules-v2')
    history=ac.client.get(f'/api/expenses/{ac.e.id}/review-history').json()
    assert history[0]['outcome']=='awaiting_reconciliation'
    assert verification(ac)['unresolved_discrepancy_count']>0
