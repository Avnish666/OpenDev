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
    def huge(*args,**kwargs):
        d=real(*args,**kwargs);d['financial_summary']['notes']=['x'*262145];return d
    monkeypatch.setattr(analytics.transparency,'overview',huge)
    assert get(ac).status_code==413


def test_filtered_grouping_uses_all_rows_not_page(ac):
    from datetime import date
    extra_expense(ac,category=' development ',amount_cents=2000,expense_date=date(2026,11,1))
    extra_expense(ac,category='Hosting',amount_cents=3000,expense_date=date(2026,11,20))
    extra_expense(ac,category='Hosting',amount_cents=9999,publication_status='draft')
    extra_expense(ac,project_id=ac.other.id,amount_cents=8888)
    d=get(ac,limit=1).json();a=d['expense_analysis']
    assert a['expense_count']==3 and a['reported_spending_cents']==6000 and len(d['expenses'])==1
    assert a['categories']==[dict(key='development',expense_count=2,amount_cents=3000),dict(key='hosting',expense_count=1,amount_cents=3000)]
    assert a['months']==[dict(key='2026-10',expense_count=1,amount_cents=1000),dict(key='2026-11',expense_count=2,amount_cents=5000)]
    filtered=get(ac,category=' DEVELOPMENT ',date_from='2026-11-01',date_to='2026-11-01').json()
    assert filtered['expense_total']==1 and filtered['expenses'][0]['amount_cents']==2000
    assert filtered['expense_analysis']['reported_spending_cents']==2000
    assert filtered['financial']['published_reported_spending_cents']==6000
    assert filtered['expense_filters']['date_from']=='2026-11-01'
    assert filtered['expense_analysis']['date_basis']=='maintainer_reported_expense_date'


def test_evidence_filter_multiple_documents_no_fanout(ac):
    original,_=receipt(ac);redacted(ac,original);redacted(ac,original)
    extra_expense(ac,amount_cents=4500)
    d=get(ac,evidence='supported').json()
    assert d['expense_total']==1 and d['expense_analysis']['reported_spending_cents']==1000
    assert d['expense_analysis']['months'][0]['expense_count']==1
    assert d['financial']['expenses_with_documents_count']==1
    assert d['financial']['expenses_with_documents_cents']==1000
    assert d['financial']['expenses_without_documents_cents']==4500
    unsupported=get(ac,evidence='unsupported').json()
    assert unsupported['expense_analysis']['reported_spending_cents']==4500
    assert unsupported['expense_analysis']['expense_count']==1
    assert all(not r['approved_public_support'] for r in unsupported['expenses'])


def test_evidence_revocation_and_unapproved_remain_unsupported(ac):
    original,_=receipt(ac);doc=redacted(ac,original);redacted(ac,original,approved=False)
    doc.publication_status='private';ac.db.commit()
    d=get(ac,evidence='supported').json()
    assert d['expense_total']==0 and d['expense_analysis']['categories']==[]
    assert d['financial']['expenses_with_documents_count']==0


@pytest.mark.parametrize('params',[
    {'date_from':'2026-02-30'}, {'date_to':'not-a-date'}, {'date_from':''},
    {'date_from':'2026-11-02','date_to':'2026-11-01'}, {'evidence':'private'},
    {'sort':'random'}, {'category':'x'*101}, {'date_to':'2026-11-01T01:00:00Z'},
])
def test_financial_filters_validated(ac,params):assert get(ac,**params).status_code==422


def test_server_date_sort_and_inclusive_pagination(ac):
    from datetime import date
    newer=extra_expense(ac,expense_date=date(2026,12,1))
    same=extra_expense(ac,expense_date=ac.e.expense_date)
    assert get(ac,sort='date_asc',limit=1,offset=0).json()['expenses'][0]['id']==ac.e.id
    assert get(ac,sort='date_asc',limit=1,offset=1).json()['expenses'][0]['id']==same.id
    assert get(ac,sort='date_desc',limit=1).json()['expenses'][0]['id']==newer.id
    assert get(ac,date_to='2026-10-31').json()['expense_total']==2
    assert get(ac,date_from='2026-12-01').json()['expense_total']==1


def test_sparse_months_no_invented_observations(ac):
    from datetime import date
    extra_expense(ac,expense_date=date(2027,2,1))
    assert [r['key'] for r in get(ac).json()['expense_analysis']['months']]==['2026-10','2027-02']
    d=get(ac,date_from='2028-01-01').json()
    assert d['expense_analysis']['months']==[] and d['expense_analysis']['reported_spending_cents']==0
    assert d['expense_total']==0


def test_no_capture_timestamp_no_funding_trend(ac):
    contribution(ac,'completed');contribution(ac,'refunded');contribution(ac,'reversed')
    for status in ['pending','denied','failed']:contribution(ac,status,99999)
    contribution(ac,'completed',99999,capture=False)
    d=get(ac).json()
    assert d['funding_trend']['available'] is False
    assert 'creation time is not capture time' in d['funding_trend']['reason']
    assert d['financial']['gross_completed_funding_cents']==6000
    assert d['financial']['net_recorded_funding_cents']==2000
    assert 'capture_id' not in str(d) and 'user_id' not in str(d)


def test_public_findings_full_project_not_duplicated_by_filtered_rows(ac):
    extra_expense(ac,amount_cents=12000)
    d=get(ac,category='no-match').json()
    assert d['expense_total']==0
    assert d['public_unresolved_finding_count']==1
    assert d['financial']['unresolved_discrepancy_count'] is None


def test_empty_project_and_zero_allocation(ac):
    ac.e.project_id=ac.other.id;ac.db.commit()
    d=get(ac).json()
    assert d['expense_analysis']['categories']==[] and d['expense_analysis']['months']==[]
    assert d['financial']['published_expense_count']==0
    extra_expense(ac,category='Unallocated',amount_cents=123)
    row=next(r for r in get(ac).json()['budget'] if r['category']=='unallocated')
    assert row['allocated_cents']==0 and row['overspend_cents']==123


def test_month_bucket_capacity_is_explicit_not_truncated(ac):
    from datetime import date
    for i in range(121):
        ac.db.add(Expense(project_id=ac.p.id,submitted_by_user_id=ac.users[0].id,category='Development',amount_cents=1,currency='USD',vendor='Synthetic',description='Synthetic',expense_date=date(2000+i//12,1+i%12,1),publication_status='published'))
    ac.db.commit()
    assert get(ac).status_code==413
    assert get(ac,date_from='2026-01-01').status_code==200


@pytest.mark.parametrize('value',[None,'2026-02-30','not-a-date'])
def test_expense_source_requires_valid_dates(value):
    from app.schemas.expense import ExpenseCreate
    from pydantic import ValidationError
    fields=dict(category='Development',amount_cents=100,currency='USD',vendor='Synthetic',description='Synthetic')
    if value is not None:fields['expense_date']=value
    with pytest.raises(ValidationError):ExpenseCreate.model_validate(fields)


def test_representative_performance_and_constant_query_count(ac):
    import json, os, time
    from pathlib import Path
    from datetime import date
    from sqlalchemy import event
    samples=[];statements=[]
    def count(*args):statements.append(1)
    event.listen(ac.engine,'before_cursor_execute',count)
    def measure(label,**params):
        statements.clear();start=time.perf_counter();response=get(ac,**params);elapsed=(time.perf_counter()-start)*1000
        assert response.status_code==200,response.text
        result=dict(workload=label,latency_ms=round(elapsed,3),sql_statements=len(statements),response_bytes=len(response.content))
        samples.append(result);return result,response.json()
    try:
        baseline,_=measure('one_expense')
        for i in range(999):
            ac.db.add(Expense(project_id=ac.p.id,submitted_by_user_id=ac.users[0].id,category=f'Category {i%12}',amount_cents=100+i,currency='USD',vendor='Synthetic',description='Synthetic',expense_date=date(2026,1+i%12,1),publication_status='published'))
        for _ in range(10):contribution(ac)
        ac.db.commit()
        for _ in range(3):
            sample,d=measure('1000_expenses_10_captures')
            assert d['expense_total']==1000 and len(d['expenses'])==50
            assert sample['sql_statements']<=baseline['sql_statements']+1
        for _ in range(3):
            sample,d=measure('1000_expenses_filtered',date_from='2026-04-01',date_to='2026-06-30')
            assert 200<d['expense_total']<300
            assert sample['sql_statements']<=baseline['sql_statements']+1
    finally:event.remove(ac.engine,'before_cursor_execute',count)
    target=os.getenv('PHASE6_PERFORMANCE_FILE')
    if target:Path(target).write_text(json.dumps(dict(environment='local TestClient/PostgreSQL16, synthetic data; cold plus warm sequential requests',samples=samples),indent=2))


def test_category_grouping_and_filter_match_authoritative_unicode_keys(ac):
    extra_expense(ac,category=' Straße ',amount_cents=100)
    extra_expense(ac,category='STRASSE',amount_cents=200)
    d=get(ac,category='strasse').json()
    assert d['expense_analysis']['categories']==[dict(key='strasse',expense_count=2,amount_cents=300)]
    assert d['expense_total']==2
    assert next(r for r in d['budget'] if r['category']=='strasse')['reported_spending_cents']==300
