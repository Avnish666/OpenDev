"""Public analytics contracts and authoritative formula reuse on isolated PostgreSQL."""
import pytest
from sqlalchemy import select,func
from app.models.expense import Expense
from app.models.funding import Contribution
from app.services import analytics
from test_accountability import ac,contribution,receipt
from test_credibility import milestone
from test_transparency import redacted,extra_expense
from test_github_progress import gh,sync

def get(ac,**params):return ac.client.get(f'/api/projects/{ac.p.id}/analytics/overview',params=params)

def test_financial_contract_and_refund_policy(ac):
    for status,amount in [('completed',20000),('refunded',3000),('reversed',4000),('pending',9000)]:contribution(ac,status,amount)
    r=get(ac);assert r.status_code==200,r.text
    d=r.json();s=d['financial']
    assert d['schema_version']=='1' and d['currency']=='USD' and d['as_of']==s['calculated_at']
    assert d['funding_goal_cents']==10000
    assert [s[k] for k in ['gross_completed_funding_cents','refund_excluded_cents','reversal_excluded_cents','net_recorded_funding_cents','published_reported_spending_cents','funding_minus_reported_expenditure_cents']]==[27000,3000,4000,20000,1000,19000]
    assert s['exact_refund_total_cents'] is None and 'Partial refund' in ' '.join(s['notes'])
    assert r.headers['cache-control']=='no-store'

def test_budget_and_expense_mapping(ac):
    extra_expense(ac,amount_cents=12000)
    d=get(ac).json();row=d['budget'][0]
    assert row==dict(category='development',allocated_cents=10000,reported_spending_cents=13000,remaining_cents=-3000,overspend_cents=3000)
    assert all(x['public_category_finding_count']==1 for x in d['expenses'])
    assert all(set(x)=={'id','category','amount_cents','currency','expense_date','approved_public_support','public_category_finding_count'} for x in d['expenses'])

def test_approved_coverage_and_private_exclusion_even_owner(ac):
    original,extraction=receipt(ac);redacted(ac,original);redacted(ac,original)
    extra_expense(ac,publication_status='draft',description='PRIVATE_DRAFT')
    for user in (ac.users[0],None):
        ac.identity[0]=user;r=get(ac);d=r.json()
        assert d['financial']['expenses_with_documents_count']==1 and d['financial']['expenses_with_documents_cents']==1000
        assert d['expenses'][0]['approved_public_support'] is True
        for secret in [original.id,extraction.id,original.storage_key,'PRIVATE_DRAFT','extracted_json','capture_id','storage_key']:
            assert secret not in r.text
        assert d['financial']['audience']=='public_evidence_only'
    assert get(ac,scope='private').status_code==422

@pytest.mark.parametrize('status',['draft','paused','completed'])
def test_nonpublic_restrictions(ac,status):
    ac.p.status=status;ac.db.commit();assert get(ac).status_code==404

def test_cross_project_paging_and_empty(ac):
    extra_expense(ac,project_id=ac.other.id,category='OTHER_PRIVATE_CATEGORY')
    extra_expense(ac,amount_cents=50)
    d=get(ac,limit=1,offset=1).json();assert d['expense_total']==2 and len(d['expenses'])==1
    assert 'OTHER_PRIVATE_CATEGORY' not in str(d)
    ac.p,ac.other=ac.other,ac.p
    assert get(ac).json()['development']['total']==0

@pytest.mark.parametrize('params',[{'limit':0},{'limit':101},{'offset':-1},{'offset':10001},{'scope':'manager_private'}])
def test_bounded_queries(ac,params):assert get(ac,**params).status_code==422

def test_development_and_owner_contract(gh):
    ac,state=gh;milestone(ac,completed='2026-10-30',status='delivered');sync(ac)
    d=get(ac).json()
    assert d['development']['counts']['delivered']==1
    assert d['development']['milestones'][0]['original_deadline']=='2026-10-31'
    assert d['development']['github_counts']['pull_requests_merged']==1
    assert d['development']['last_successful_sync_at']
    assert d['maintainer']['owner_id']==ac.p.owner_id
    assert next(m for m in d['maintainer']['delivery'] if m['key']=='asserted_delivered')['numerator']==1
    assert 'owned' in d['maintainer']['attribution']

def test_no_financial_writes(ac):
    c=contribution(ac);before=(c.amount_cents,c.status,ac.e.amount_cents,ac.db.scalar(select(func.count()).select_from(Contribution)))
    assert get(ac).status_code==200
    ac.db.refresh(c);ac.db.refresh(ac.e)
    assert before==(c.amount_cents,c.status,ac.e.amount_cents,ac.db.scalar(select(func.count()).select_from(Contribution)))
    assert ac.client.post(f'/api/projects/{ac.p.id}/analytics/overview',json={}).status_code==405

def test_response_cap(ac,monkeypatch):
    real=analytics.transparency.overview
    def huge(*args):
        d=real(*args);d['financial_summary']['notes']=['x'*262145];return d
    monkeypatch.setattr(analytics.transparency,'overview',huge)
    assert get(ac).status_code==413
