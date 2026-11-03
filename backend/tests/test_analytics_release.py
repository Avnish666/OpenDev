"""Scoped final analytics audit, reproducible local benchmarks and real browser bridge."""
import csv,io,json,os,statistics,time,tracemalloc
from pathlib import Path
from datetime import date
from uuid import uuid4
import pytest
from sqlalchemy import event,select,func
from app.models.expense import Expense
from app.models.funding import Entitlement
from app.services import analytics_exports as exports
from test_accountability import ac,contribution,receipt
from test_credibility import milestone
from test_transparency import extra_expense,redacted
from test_github_progress import gh,sync

@pytest.fixture(autouse=True)
def clear_quota():exports._peers.clear();yield;exports._peers.clear()

def test_concurrent_admission_and_cleanup(ac,monkeypatch):
    exports.admit('slot-one');exports.admit('slot-two')
    try:
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:exports.admit('slot-three')
        assert exc.value.status_code==429
    finally:exports._slots.release();exports._slots.release()
    def fail(*args,**kwargs):raise TimeoutError('PRIVATE_TIMEOUT')
    monkeypatch.setattr(exports,'generate',fail)
    r=ac.client.get(f'/api/projects/{ac.p.id}/analytics/export/expenses')
    assert r.status_code==503 and 'PRIVATE_TIMEOUT' not in r.text
    exports.admit('after-error');exports._slots.release()

@pytest.mark.parametrize('count',[1,100,200,1000])
def test_final_analytics_benchmark(ac,count):
    for i in range(count-1):ac.db.add(Expense(project_id=ac.p.id,submitted_by_user_id=ac.users[0].id,category='Development',amount_cents=100,currency='USD',vendor='Synthetic',description='Synthetic row',expense_date=date(2026,10,31),publication_status='published'))
    ac.db.commit()
    values=[]
    for kind,path in [('analytics',f'/api/projects/{ac.p.id}/analytics/overview'),('export',f'/api/projects/{ac.p.id}/analytics/export/expenses')]:
        ac.client.get(path);times=[];sizes=[];queries=[]
        tracemalloc.start()
        for _ in range(10):
            exports._peers.clear();sql=[]
            def capture(*args):sql.append(1)
            event.listen(ac.engine,'before_cursor_execute',capture);start=time.perf_counter()
            try:r=ac.client.get(path)
            finally:event.remove(ac.engine,'before_cursor_execute',capture)
            assert r.status_code==200,r.text
            times.append(round((time.perf_counter()-start)*1000,3));sizes.append(len(r.content));queries.append(len(sql))
            if kind=='export':assert len(list(csv.DictReader(io.StringIO(r.content.decode('utf-8-sig')))))==count
        _,peak=tracemalloc.get_traced_memory();tracemalloc.stop()
        values.append(dict(kind=kind,rows=count,samples_ms=times,median_ms=statistics.median(times),empirical_p95_ms=sorted(times)[-1],sql=queries,bytes=max(sizes),peak_traced_python_bytes=peak))
    target=os.getenv('PHASE6_AUDIT_DIR')
    if target:Path(target).mkdir(parents=True,exist_ok=True);Path(target,f'analytics-{count}.json').write_text(json.dumps(values,indent=2))


def test_real_public_analytics_journey(gh):
    ac,state=gh;sync(ac)
    for status,amount in [('completed',3000),('completed',3000),('refunded',1000),('reversed',500)]:
        c=contribution(ac,status,amount)
        if status=='completed':ac.db.add(Entitlement(id=str(uuid4()),contribution_id=c.id,status='fulfilled' if amount and ac.db.scalar(select(func.count()).select_from(Entitlement))==0 else 'granted',fulfillment_note='PRIVATE_BACKER_NOTE'));ac.db.commit()
    extra_expense(ac,category='Hosting',amount_cents=1500)
    original,record=receipt(ac);redacted(ac,original);redacted(ac,original)
    milestone(ac,completed='2026-11-01',current='2026-12-01',status='delivered');milestone(ac,status='in_progress');milestone(ac,status='cancelled')
    before=(ac.e.amount_cents,ac.db.scalar(select(func.count()).select_from(Entitlement)))
    ac.other.status='draft';ac.db.commit()
    ac.identity[0]=None
    from app.main import app
    from app.core.auth import get_current_user
    app.dependency_overrides.pop(get_current_user,None)
    if os.getenv('PHASE6_BROWSER_JOURNEY')=='1':
        import socket,threading,subprocess,uvicorn
        listener=socket.socket();listener.bind(('127.0.0.1',0));listener.listen(128)
        server=uvicorn.Server(uvicorn.Config(app,log_level='critical',access_log=False,timeout_graceful_shutdown=5));thread=threading.Thread(target=server.run,kwargs={'sockets':[listener]},daemon=True);thread.start()
        try:
            for _ in range(100):
                if server.started:break
                time.sleep(.05)
            assert server.started
            env=dict(os.environ,PHASE6_TEST_API=f'http://127.0.0.1:{listener.getsockname()[1]}',PHASE6_TEST_PROJECT=str(ac.p.id),PHASE6_PRIVATE_PROJECT=str(ac.other.id),VITE_API_URL='')
            subprocess.run(['node','tests/browser-analytics-journey.mjs'],cwd=Path(__file__).parents[2]/'frontend',env=env,timeout=120,check=True)
        finally:server.should_exit=True;thread.join(10);listener.close()
        assert not thread.is_alive()
    else:
        r=ac.client.get(f'/api/projects/{ac.p.id}/analytics/overview');assert r.status_code==200
        assert r.json()['financial']['net_recorded_funding_cents']==6000
        assert original.id not in r.text and record.id not in r.text
    ac.db.refresh(ac.e);assert before==(ac.e.amount_cents,ac.db.scalar(select(func.count()).select_from(Entitlement)))

def test_large_development_benchmark(gh):
    from datetime import datetime,timezone
    from app.models.github_progress import GitHubIssueSnapshot as Issue,GitHubPullRequestSnapshot as Pull
    from app.models.roadmap import ProjectRoadmapMilestone as Milestone,MilestoneStatusHistory as History
    ac,state=gh;sync(ac);now=datetime.now(timezone.utc)
    milestones=[Milestone(project_id=ac.p.id,title=f'Synthetic {i}',description='Synthetic audit',deliverable_description='Synthetic result',planned_start_date=date(2026,1,1),planned_end_date=date(2026,12,31),status='planned',version=1,created_by=ac.users[0].id) for i in range(500)]
    ac.db.add_all(milestones);ac.db.flush()
    ac.db.add_all([History(id=str(uuid4()),milestone_id=m.id,version=1,previous_status=None,new_status='planned',actor_id=ac.users[0].id,action='created',reason='Synthetic audit',before_json={},after_json={'planned_end_date':'2026-12-31','status':'planned'}) for m in milestones])
    for model,count,base in [(Issue,2000,10000),(Pull,1000,20000)]:
        for i in range(count):
            values=dict(project_id=ac.p.id,github_id=base+i,number=100+i,title='Synthetic observed text',state='closed' if i%2 else 'open',created_at=now,updated_at=now,last_synced_at=now)
            if model is Pull:values['merged_at']=now if i%2 else None
            ac.db.add(model(**values))
    ac.db.commit();times=[];queries=[];sizes=[]
    for _ in range(10):
        sql=[]
        def capture(*args):sql.append(1)
        event.listen(ac.engine,'before_cursor_execute',capture);start=time.perf_counter()
        try:r=ac.client.get(f'/api/projects/{ac.p.id}/analytics/overview')
        finally:event.remove(ac.engine,'before_cursor_execute',capture)
        assert r.status_code==200,r.text
        assert r.json()['development']['total']==500
        times.append(round((time.perf_counter()-start)*1000,3));queries.append(len(sql));sizes.append(len(r.content))
    assert len(set(queries))==1
    target=os.getenv('PHASE6_AUDIT_DIR')
    if target:Path(target).mkdir(parents=True,exist_ok=True);Path(target,'large-development.json').write_text(json.dumps(dict(milestones=500,issues=2001,pulls=1001,samples_ms=times,median_ms=statistics.median(times),empirical_p95_ms=max(times),sql=queries,bytes=max(sizes)),indent=2))
