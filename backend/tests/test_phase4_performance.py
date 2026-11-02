"""Reproducible synthetic HTTP benchmarks; query bounds, never timing assertions."""
import json
import os
import platform
import resource
import statistics
import time
from datetime import date, datetime, timezone
from pathlib import Path
from uuid import uuid4
import pytest
from sqlalchemy import event
from app.models.project import Project
from app.models.budget_allocation import BudgetAllocation
from app.models.expense import Expense
from app.models.roadmap import ProjectRoadmapMilestone as Milestone, MilestoneStatusHistory as History
from app.models.github_progress import GitHubRepositorySnapshot as Repo, GitHubSyncRun as Run, GitHubIssueSnapshot as Issue, GitHubPullRequestSnapshot as Pull
from test_accountability import ac


def measure(ac,path):
    # Warm one request, then measure three complete local TestClient HTTP responses.
    assert ac.client.get(path).status_code==200
    timings=[];counts=[];sizes=[]
    for _ in range(3):
        queries=[]
        def capture(*args):queries.append(1)
        event.listen(ac.engine,'before_cursor_execute',capture)
        start=time.perf_counter()
        try:response=ac.client.get(path)
        finally:event.remove(ac.engine,'before_cursor_execute',capture)
        timings.append(round((time.perf_counter()-start)*1000,2));counts.append(len(queries));sizes.append(len(response.content))
        assert response.status_code==200,response.text
    assert len(set(counts))==1
    return dict(query_count=counts[0],median_ms=statistics.median(timings),samples_ms=timings,response_bytes=max(sizes))


@pytest.mark.parametrize('project_count',[1,8])
def test_synthetic_progress_and_credibility_benchmark(ac,tmp_path,project_count):
    now=datetime.now(timezone.utc)
    projects=[ac.p]
    for index in range(1,project_count):
        p=Project(owner_id=ac.users[0].id,github_repo_id=10000+index,github_repo_url=f'https://github.com/owner/synthetic-{index}',title=f'Synthetic project {index}',description='Benchmark fixture only',funding_goal_cents=10000,currency='USD',status='active')
        ac.db.add(p);projects.append(p)
    ac.db.flush()
    for index,p in enumerate(projects):
        if index:ac.db.add(BudgetAllocation(project_id=p.id,category='Development',allocated_cents=10000))
        ac.db.add(Repo(project_id=p.id,github_repo_id=p.github_repo_id,metadata_json={'id':p.github_repo_id,'full_name':f'owner/synthetic-{index}','private':False,'default_branch':'main','updated_at':now.isoformat(),'pushed_at':now.isoformat()},publicly_accessible=True,recent_commits=[{'sha':'a'*40,'committed_at':now.isoformat()}],last_synced_at=now))
        ac.db.add(Run(id=str(uuid4()),project_id=p.id,status='completed',started_at=now,completed_at=now,counters={}))
        for j in range(35):
            row=Milestone(project_id=p.id,title=f'Synthetic commitment {j}',description='Local benchmark',deliverable_description='Synthetic documented release',planned_start_date=date(2026,1,1),planned_end_date=date(2026,12,31),status='planned',version=1,created_by=ac.users[0].id)
            ac.db.add(row);ac.db.flush()
            ac.db.add(History(id=str(uuid4()),milestone_id=row.id,version=1,previous_status=None,new_status='planned',actor_id=ac.users[0].id,action='created',reason='Synthetic benchmark commitment only',before_json={},after_json={'status':'planned','planned_end_date':'2026-12-31'}))
        for j in range(20):ac.db.add(Expense(project_id=p.id,submitted_by_user_id=ac.users[0].id,category='Development',amount_cents=100,currency='USD',vendor='Synthetic vendor',description='Benchmark reported expense only',expense_date=date(2026,10,31),publication_status='published'))
        for j in range(80):ac.db.add(Issue(project_id=p.id,github_id=100000+index*1000+j,number=j+1,title='Synthetic issue',state='closed' if j%2 else 'open',created_at=now,updated_at=now,last_synced_at=now))
        for j in range(40):ac.db.add(Pull(project_id=p.id,github_id=200000+index*1000+j,number=100+j,title='Synthetic pull request',state='closed',created_at=now,updated_at=now,merged_at=now if j%2 else None,last_synced_at=now))
    ac.db.commit();ac.identity[0]=None
    results={
        'scenario':dict(owned_projects=project_count,milestones=35*project_count,histories=35*project_count,published_expenses=20*project_count+1,issue_snapshots=80*project_count,pr_snapshots=40*project_count,contributions=0,documents=0),
        'hardware':dict(platform=platform.platform(),python=platform.python_version(),logical_cpus=os.cpu_count()),
        'progress_summary':measure(ac,f'/api/projects/{ac.p.id}/progress-summary'),
        'credibility':measure(ac,f'/api/maintainers/{ac.users[0].id}/credibility'),
        'delivery_page':measure(ac,f'/api/maintainers/{ac.users[0].id}/delivery-history?limit=100'),
    }
    results['process_peak_rss_kib']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    # Bounds depend on query structure, not deployment speed or row count.
    assert results['progress_summary']['query_count']<=45
    assert results['delivery_page']['query_count']<=12
    output=Path(os.getenv('PHASE4_BENCHMARK_DIR',str(tmp_path)));output.mkdir(parents=True,exist_ok=True)
    (output/f'phase4-{project_count}-projects.json').write_text(json.dumps(results,indent=2)+'\n')
    print(json.dumps(results))
