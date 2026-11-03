"""Small synthetic local workload benchmark; no live model/provider or production DB."""
import json,os,resource,statistics,time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from sqlalchemy import event
from app.agent import limits
from app.services import analytics_exports
from test_accountability import ac,contribution
from test_credibility import milestone
from test_agent_orchestration import Replay


def test_local_read_only_capacity(ac,monkeypatch):
    contribution(ac);milestone(ac)
    monkeypatch.setattr(limits,'limiter',limits.RateLimiter())
    monkeypatch.setattr('app.agent.orchestration.OllamaProvider',lambda *args:Replay(available=False))
    workloads=[('project','GET',f'/api/projects/{ac.p.id}',None),('financial_analytics','GET',f'/api/projects/{ac.p.id}/analytics/overview',None),('development','GET',f'/api/projects/{ac.p.id}/progress-summary',None),('agent_deterministic','POST',f'/api/projects/{ac.p.id}/agent/query',{'project_id':ac.p.id,'question':'funding','mode':'deterministic'}),('csv','GET',f'/api/projects/{ac.p.id}/analytics/export/financial',None)]
    output=[];before=resource.getrusage(resource.RUSAGE_SELF)
    try:
        for name,method,path,body in workloads:
            samples=[]
            for _ in range(10):
                analytics_exports._peers.clear();count=[0]
                def sql(*args):count[0]+=1
                event.listen(ac.engine,'before_cursor_execute',sql);start=time.perf_counter()
                try:r=ac.client.request(method,path,json=body)
                finally:event.remove(ac.engine,'before_cursor_execute',sql)
                assert r.status_code==200,r.text
                samples.append({'ms':round((time.perf_counter()-start)*1000,3),'sql_statements':count[0],'bytes':len(r.content)})
            output.append({'workload':name,'n':10,'median_ms':statistics.median(x['ms'] for x in samples),'empirical_p95_ms':max(x['ms'] for x in samples),'samples':samples,'errors':0})
        def read(_):
            start=time.perf_counter();r=ac.client.get(f'/api/projects/{ac.p.id}');assert r.status_code==200
            return round((time.perf_counter()-start)*1000,3)
        with ThreadPoolExecutor(max_workers=4) as pool:batch=list(pool.map(read,range(12)))
        r=ac.client.post(f'/api/projects/{ac.p.id}/agent/query',json={'project_id':ac.p.id,'question':'funding','mode':'auto'})
        assert r.status_code==200 and r.json()['execution_mode']=='deterministic'
        after=resource.getrusage(resource.RUSAGE_SELF)
        result={'scope':'Synthetic PostgreSQL TestClient; external model outage mocked; not Render or real inference','workloads':output,'concurrent_project_reads':{'workers':4,'n':12,'errors':0,'median_ms':statistics.median(batch),'max_ms':max(batch)},'auto_outage_actual_mode':r.json()['execution_mode'],'test_process_cpu_seconds':round(after.ru_utime+after.ru_stime-before.ru_utime-before.ru_stime,3),'cumulative_test_process_peak_rss_kib':after.ru_maxrss,'limits':'Ten samples: empirical p95 equals maximum, not a production percentile estimate. SQL excludes driver controls. RSS is cumulative pytest peak; DB/model CPU/RAM excluded.'}
        if os.getenv('PHASE7_CAPACITY_DIR'):
            p=Path(os.environ['PHASE7_CAPACITY_DIR']);p.mkdir(parents=True,exist_ok=True);(p/'phase7-ai-local-capacity.json').write_text(json.dumps(result,indent=2)+'\n')
    finally:analytics_exports._peers.clear()
