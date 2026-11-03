from datetime import date
import pytest
from test_accountability import ac
from test_credibility import milestone
from test_transparency import extra_expense
from test_analytics import get
from test_github_progress import gh,sync

@pytest.mark.parametrize('params',[{'milestone_status':'bogus'},{'delivery':'yes'},{'outcome':'verified'},{'planned_from':'2026-02-30'},{'planned_from':'2026-12-01','planned_to':'2026-01-01'},{'github_category':'private'},{'github_freshness':'live'},{'discrepancy':'private'}])
def test_invalid(ac,params):assert get(ac,**params).status_code==422

def test_milestone_filters_full_counts_before_page(ac):
    for _ in range(3):milestone(ac,status='in_progress')
    milestone(ac,status='cancelled')
    d=get(ac,milestone_status='in_progress',limit=1).json()
    assert d['development']['total']==3 and len(d['development']['milestones'])==1
    assert d['development']['counts']['overdue_unfinished']==3
    assert get(ac,delivery='delivered').json()['development']['total']==0
    assert get(ac,planned_from='2026-10-31',planned_to='2026-10-31').json()['development']['total']==4

def test_discrepancy_rows_groups_full_money(ac):
    extra_expense(ac,amount_cents=12000)
    from app.models.budget_allocation import BudgetAllocation
    ac.db.add(BudgetAllocation(project_id=ac.p.id,category='Other',allocated_cents=100));ac.db.commit()
    extra_expense(ac,category='Other',amount_cents=100)
    d=get(ac,discrepancy='with').json();assert d['expense_total']==2
    assert d['expense_analysis']['reported_spending_cents']==13000
    assert d['financial']['published_reported_spending_cents']==13100
    assert get(ac,discrepancy='without').json()['expense_analysis']['reported_spending_cents']==100
    assert get(ac,discrepancy='with',category='Other').json()['expense_total']==0

def test_github_type_and_observation_age(gh):
    ac,s=gh;sync(ac)
    d=get(ac,github_category='issue',github_freshness='current').json()['development']['github']
    assert d['counts']=={'issues_open':1,'issues_closed':0}
    assert not d['pull_requests'] and not d['recent_commits']
    d=get(ac,github_freshness='stale').json()['development']['github']
    assert all(v==0 for v in d['counts'].values()) and not d['issues']

def test_owner_history_not_replaced_by_current_filter(ac):
    milestone(ac,completed='2026-11-01',status='delivered')
    d=get(ac,milestone_status='planned').json()
    assert d['development']['total']==0
    assert next(m for m in d['maintainer']['delivery'] if m['key']=='asserted_delivered')['numerator']==1
