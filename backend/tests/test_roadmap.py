from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timezone, timedelta
from sqlalchemy import select, func, text
from sqlalchemy.exc import DBAPIError
import pytest
from app.models.roadmap import ProjectRoadmapMilestone as Milestone, MilestoneGitHubEvidence as Evidence, MilestoneStatusHistory as History
from app.models.github_progress import GitHubRepositorySnapshot as Repo, GitHubIssueSnapshot as Issue, GitHubPullRequestSnapshot as Pull
from test_github_progress import gh, sync
from test_accountability import ac, contribution

BODY=dict(title='Beta release',description='Public beta commitment',deliverable_description='Publish a documented beta package',planned_start_date='2026-11-01',planned_end_date='2026-12-01')
REASON='A public explanation for this recorded decision.'


def ok(response,status=200):
    assert response.status_code==status,response.text
    return response.json()


def create(ac,**values):
    return ok(ac.client.post(f'/api/projects/{ac.p.id}/roadmap',json={**BODY,**values}),201)


def action(ac,row,state,**values):
    return ac.client.post(f"/api/roadmap/{row['id']}/status",json=dict(status=state,expected_version=row['version'],reason=REASON,**values))


def link(ac,row,kind='issue',canonical='201'):
    return ac.client.post(f"/api/roadmap/{row['id']}/evidence",json=dict(evidence_type=kind,canonical_id=canonical,expected_version=row['version'],reason=REASON))


def listing(ac):return ok(ac.client.get(f'/api/projects/{ac.p.id}/roadmap'))


@pytest.mark.parametrize('actor',[0,1])
def test_authorized_creation_and_append_only_history(ac,actor):
    ac.identity[0]=ac.users[actor];row=create(ac)
    assert row['status']=='planned' and row['version']==1
    history=ok(ac.client.get(f"/api/roadmap/{row['id']}/history"))
    assert history[0]['after']['deliverable_description']==BODY['deliverable_description']
    for statement in ['UPDATE milestone_status_history SET reason=\'tampered\'','DELETE FROM milestone_status_history']:
        with pytest.raises(DBAPIError):
            with ac.db.begin_nested():ac.db.execute(text(statement))


@pytest.mark.parametrize('actor',[2,3])
def test_unauthorized_edits(ac,actor):
    row=create(ac);ac.identity[0]=ac.users[actor]
    assert ac.client.patch(f"/api/roadmap/{row['id']}",json={'expected_version':1,'reason':REASON,'title':'Unauthorized'}).status_code==403
    assert action(ac,row,'in_progress').status_code==403
    assert link(ac,row).status_code==403
    assert ac.client.post(f'/api/projects/{ac.p.id}/roadmap',json=BODY).status_code==403


@pytest.mark.parametrize('changes',[{'planned_start_date':'2027-01-01'},{'planned_end_date':'bad-date'},{'display_order':-1}])
def test_invalid_creation(ac,changes):
    assert ac.client.post(f'/api/projects/{ac.p.id}/roadmap',json={**BODY,**changes}).status_code==422


def test_dates_ordering_and_published_commitment_history(ac):
    first=create(ac,display_order=10);second=create(ac,display_order=0)
    assert [r['id'] for r in listing(ac)['items']]==[second['id'],first['id']]
    path=f"/api/roadmap/{first['id']}"
    assert ac.client.patch(path,json={'expected_version':1,'reason':REASON,'planned_end_date':'2026-10-01'}).status_code==422
    assert ac.client.patch(path,json={'expected_version':1,'title':'Changed promise'}).status_code==422
    changed=ok(ac.client.patch(path,json={'expected_version':1,'reason':REASON,'title':'Changed promise','display_order':0}))
    assert changed['version']==2
    assert [r['id'] for r in listing(ac)['items']]==[first['id'],second['id']]
    history=ok(ac.client.get(path+'/history'))
    assert history[0]['before']['title']=='Beta release' and history[0]['after']['title']=='Changed promise'
    assert history[0]['reason']==REASON
    assert ac.client.patch(path,json={'expected_version':1,'reason':REASON,'title':'Stale overwrite'}).status_code==409


def test_issue_pr_milestone_commit_links_and_duplicates(gh):
    ac,s=gh;ok(sync(ac));row=create(ac)
    for kind,canonical in [('issue','201'),('pull_request','301'),('github_milestone','101'),('commit','a'*40)]:
        row=ok(link(ac,row,kind,canonical))
    signals=row['development_signals']
    assert signals['linked_issues']==1 and signals['merged_pull_requests']==1 and signals['linked_commits']==1
    assert row['status']=='planned' and row['actual_completion_date'] is None
    assert link(ac,row).status_code==409
    assert ac.db.scalar(select(func.count()).select_from(Evidence))==4
    pr=ac.db.get(Pull,(ac.p.id,301));pr.merged_at=None;ac.db.commit()
    assert listing(ac)['items'][0]['development_signals']['merged_pull_requests']==0


@pytest.mark.parametrize('kind,canonical',[('issue','https://github.com/owner/repo/issues/2'),('issue','2'),('commit','b'*40),('issue','0201')])
def test_unverified_identifiers_rejected(gh,kind,canonical):
    ac,s=gh;ok(sync(ac));row=create(ac)
    assert link(ac,row,kind,canonical).status_code==422


def test_cross_project_and_cross_milestone_binding_rejected(gh):
    ac,s=gh;ok(sync(ac));row=create(ac)
    ac.db.add(Issue(project_id=ac.other.id,github_id=999,number=1,title='Other private source',state='closed',created_at=datetime.now(timezone.utc),updated_at=datetime.now(timezone.utc),last_synced_at=datetime.now(timezone.utc)));ac.db.commit()
    assert link(ac,row,'issue','999').status_code==422
    linked=ok(link(ac,row));eid=linked['evidence'][0]['id'];other=create(ac)
    response=ac.client.request('DELETE',f"/api/roadmap/{other['id']}/evidence/{eid}",json={'expected_version':other['version'],'reason':REASON})
    assert response.status_code==404


def test_transitions_explicit_delivery_and_reopening(gh):
    ac,s=gh;ok(sync(ac));row=create(ac)
    assert action(ac,row,'delivered').status_code==409
    row=ok(action(ac,row,'in_progress'))
    assert action(ac,row,'submitted_for_review').status_code==409
    row=ok(link(ac,row));row=ok(action(ac,row,'submitted_for_review'))
    assert row['status']=='submitted_for_review' and row['actual_completion_date'] is None
    row=ok(action(ac,row,'delivered'));assert row['actual_completion_date']==date.today().isoformat()
    assert ac.client.patch(f"/api/roadmap/{row['id']}",json={'expected_version':row['version'],'reason':REASON,'title':'Rewrite delivery'}).status_code==409
    row=ok(action(ac,row,'in_progress'));assert row['actual_completion_date'] is None
    history=ok(ac.client.get(f"/api/roadmap/{row['id']}/history"))
    assert any(h['after'].get('actual_completion_date') for h in history)


def test_unlink_soft_removal_relink_and_audit(gh):
    ac,s=gh;ok(sync(ac));row=ok(link(ac,create(ac)));eid=row['evidence'][0]['id']
    row=ok(ac.client.request('DELETE',f"/api/roadmap/{row['id']}/evidence/{eid}",json={'expected_version':row['version'],'reason':REASON}))
    assert not row['evidence']
    assert ac.db.get(Evidence,eid).removed_at is not None
    row=ok(link(ac,row));assert row['evidence'][0]['id']==eid
    assert ac.db.scalar(select(func.count()).select_from(Evidence))==1
    assert any(h['action']=='evidence_removed' for h in ok(ac.client.get(f"/api/roadmap/{row['id']}/history")))


def test_stale_rename_retained_commit_and_inaccessible_repository(gh):
    ac,s=gh;ok(sync(ac));row=ok(link(ac,create(ac),'commit','a'*40))
    repo=ac.db.get(Repo,ac.p.id);repo.metadata_json={**repo.metadata_json,'full_name':'renamed/project'};repo.recent_commits=[];ac.db.commit()
    evidence=listing(ac)['items'][0]['evidence'][0]
    assert evidence['stale'] and not evidence['snapshot_available'] and '/renamed/project/commit/' in evidence['url']
    row=ok(link(ac,row,'issue','201'))
    item=ac.db.get(Issue,(ac.p.id,201));item.last_synced_at=datetime.now(timezone.utc)-timedelta(days=1);ac.db.commit()
    assert next(e for e in listing(ac)['items'][0]['evidence'] if e['evidence_type']=='issue')['stale']
    repo.publicly_accessible=False;ac.db.commit();ac.identity[0]=None
    assert all(e['url'] is None and e['canonical_id'] is None and e['stale'] for e in listing(ac)['items'][0]['evidence'])
    history=ok(ac.client.get(f"/api/roadmap/{row['id']}/history"))
    assert 'aaaaaaaa' not in str(history) and 'canonical_id' not in str(history)


@pytest.mark.parametrize('state',['draft','paused','completed'])
def test_public_visibility(ac,state):
    row=create(ac);ac.p.status=state;ac.db.commit()
    assert ac.client.get(f'/api/projects/{ac.p.id}/roadmap').status_code==200
    ac.identity[0]=None
    assert ac.client.get(f'/api/projects/{ac.p.id}/roadmap').status_code==404
    assert ac.client.get(f"/api/roadmap/{row['id']}/history").status_code==404


def test_concurrent_status_versions(ac):
    row=create(ac)
    with ThreadPoolExecutor(max_workers=2) as pool:responses=list(pool.map(lambda _:action(ac,row,'in_progress'),range(2)))
    assert sorted(r.status_code for r in responses)==[200,409]
    assert ac.db.scalar(select(func.count()).select_from(History))==2


def test_financial_invariance_and_csrf(ac):
    payment=contribution(ac);before=(payment.amount_cents,payment.status,ac.e.amount_cents,ac.e.evidence_status)
    row=create(ac);ok(action(ac,row,'in_progress'))
    ac.db.refresh(payment);ac.db.refresh(ac.e)
    assert (payment.amount_cents,payment.status,ac.e.amount_cents,ac.e.evidence_status)==before
    assert ac.client.post(f'/api/projects/{ac.p.id}/roadmap',json=BODY,headers={'Origin':'https://evil.invalid'}).status_code==403
    assert ac.client.post(f"/api/roadmap/{row['id']}/status",json={'expected_version':2,'reason':REASON,'status':'cancelled'},headers={'Origin':''}).status_code==403
