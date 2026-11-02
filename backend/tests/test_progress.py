from datetime import datetime, timezone, timedelta
from sqlalchemy import select, func, event
import pytest
from app.models.roadmap import ProjectRoadmapMilestone as Milestone, MilestoneStatusHistory as History
from app.models.github_progress import GitHubRepositorySnapshot as Repo
from test_accountability import ac, contribution, receipt, decision, verification
from test_github_progress import gh, sync
from test_credibility import milestone
from test_transparency import redacted, extra_expense


def summary(ac):
    result=ac.client.get(f'/api/projects/{ac.p.id}/progress-summary');assert result.status_code==200,result.text
    assert result.headers['cache-control']=='no-store';return result.json()


def test_public_empty_summary_and_financial_reuse(ac):
    ac.identity[0]=None;data=summary(ac)
    assert data['counts']['total']==0 and data['owner']['delivery']['total']==0
    assert data['activity'] is None and data['sync']['stale']
    assert data['sync']['latest'] is None and data['snapshot_age_seconds'] is None
    finance=ac.client.get(f'/api/projects/{ac.p.id}/transparency').json()['financial_summary']
    for key in ['net_recorded_funding_cents','published_reported_spending_cents','expenses_with_documents_count']:
        assert data['financial'][key]==finance[key]


@pytest.mark.parametrize('state',['draft','paused','completed'])
def test_non_active_denied_even_to_owner(ac,state):
    ac.p.status=state;ac.db.commit()
    assert ac.client.get(f'/api/projects/{ac.p.id}/progress-summary').status_code==404
    ac.identity[0]=None;assert ac.client.get(f'/api/projects/{ac.p.id}/progress-summary').status_code==404


def test_counts_original_deadlines_reopen_and_overdue(ac):
    milestone(ac,original='2026-10-01',current='2026-12-01',completed='2026-11-01',status='delivered')
    milestone(ac,completed='2026-10-30',status='in_progress',reopened=True)
    milestone(ac,status='cancelled');milestone(ac);milestone(ac,status='submitted_for_review')
    data=summary(ac);c=data['counts']
    assert c['total']==5 and c['delivered']==1 and c['in_progress']==1 and c['cancelled']==1 and c['submitted_for_review']==1
    assert c['on_time']==0 and c['late']==1 and c['reopened']==1 and c['overdue_unfinished']==3
    late=next(r for r in data['delivery_history_preview'] if r['status']=='delivered')
    assert late['original_deadline']=='2026-10-01' and late['current_deadline']=='2026-12-01'
    assert data['recent_changes'][0]['reason']=='Synthetic immutable public history'
    assert data['roadmap_updated_at']


def test_fresh_sync_failure_retains_public_activity_and_separate_times(gh):
    ac,s=gh;sync(ac);fresh=summary(ac)
    assert fresh['github_available'] and not fresh['sync']['stale']
    assert fresh['activity']['pull_requests'][0]['merged_at']
    assert fresh['sync']['latest']['status']=='completed' and fresh['snapshot_age_seconds']>=0
    s['code']=500;sync(ac);failed=summary(ac)
    assert failed['activity']['issues']==fresh['activity']['issues']
    assert failed['sync']['stale'] and failed['sync']['latest']['status']=='failed'
    assert failed['sync']['last_successful_sync_at']==fresh['sync']['last_successful_sync_at']
    assert failed['calculated_at']!=failed['sync']['last_successful_sync_at']


def test_known_private_repo_sources_withheld_but_public_commitments_remain(gh):
    ac,s=gh;sync(ac);milestone(ac);repo=ac.db.get(Repo,ac.p.id);repo.publicly_accessible=False;ac.db.commit()
    data=summary(ac)
    assert not data['github_available'] and data['activity'] is None and data['github_milestones']==[]
    assert data['linked_issues'] is None and data['linked_merged_pull_requests'] is None
    assert 'counters' not in data['sync'].get('latest',{}) and data['counts']['total']==1
    assert 'owner/repo' not in str(data)


def test_unique_linked_counts_and_safe_public_change_projection(gh):
    from test_roadmap import create, link, ok
    ac,s=gh;sync(ac)
    for _ in range(2):
        row=ok(link(ac,create(ac)));ok(link(ac,row,'pull_request','301'))
    data=summary(ac)
    assert data['linked_issues']==1 and data['linked_merged_pull_requests']==1
    assert all('evidence' not in str(h['before'])+str(h['after']) for h in data['recent_changes'])
    assert data['counts']['delivered']==0


def test_privacy_cross_project_and_records_unchanged(ac):
    c=contribution(ac);doc,record=receipt(ac);decision(ac,verification(ac)['findings'][0]);redacted(ac,doc)
    milestone(ac)
    private=extra_expense(ac,vendor='PRIVATE_DRAFT_VENDOR',publication_status='draft')
    other=extra_expense(ac,project_id=ac.other.id,vendor='OTHER_PROJECT_VENDOR')
    before=(c.status,c.amount_cents,ac.e.amount_cents,ac.db.scalar(select(func.count()).select_from(History)))
    data=summary(ac)
    for value in [doc.id,record.id,doc.storage_key,'PRIVATE_DRAFT_VENDOR','OTHER_PROJECT_VENDOR','Synthetic private review']:
        assert value not in str(data)
    assert data['financial']['expenses_with_documents_count']==1
    ac.db.refresh(c);ac.db.refresh(ac.e)
    assert before==(c.status,c.amount_cents,ac.e.amount_cents,ac.db.scalar(select(func.count()).select_from(History)))
    assert ac.client.post(f'/api/projects/{ac.p.id}/progress-summary',json={'delivered':True}).status_code==405
    assert ac.client.get('/api/projects/9999999/progress-summary').status_code==404


def test_public_summary_query_count_does_not_grow_per_expense_or_milestone(ac):
    milestone(ac);milestone(ac)
    def query_count():
        calls=[]
        def capture(*args):calls.append(1)
        event.listen(ac.engine,'before_cursor_execute',capture)
        try:summary(ac)
        finally:event.remove(ac.engine,'before_cursor_execute',capture)
        return len(calls)
    baseline=query_count()
    for _ in range(12):milestone(ac);extra_expense(ac)
    assert query_count()==baseline


def test_recent_sync_does_not_hide_stale_linked_sources(gh):
    from test_roadmap import create, link, ok
    from app.models.github_progress import GitHubIssueSnapshot as Issue
    ac,s=gh;sync(ac);ok(link(ac,create(ac)))
    source=ac.db.get(Issue,(ac.p.id,201));source.last_synced_at=datetime.now(timezone.utc)-timedelta(days=2);ac.db.commit()
    data=summary(ac)
    assert not data['sync']['stale'] and data['linked_evidence_stale'] is True
