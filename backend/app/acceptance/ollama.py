"""Loopback-only model detection/benchmarks. Never pulls weights or exposes a server."""
import argparse,asyncio,json,os,re,resource,shutil,time
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlsplit
import httpx
from app.agent.providers import OllamaProvider,ProviderError

QUESTIONS=[('funding','How much funding has this project received?'),('expenses','Which expenses have public supporting documents?'),('budget','Is reported spending above the budget?'),('roadmap','Which milestones are overdue?'),('github','What GitHub activity is recorded?'),('maintainer','What is the maintainer track record?'),('rewards','What rewards have been fulfilled?'),('cross_domain','Compare funding with overdue roadmap commitments.')]


def local_endpoint(base,model):
    OllamaProvider(base,model or 'probe-only')
    if model and (model.lower().endswith('-cloud') or model.lower().endswith(':cloud')):
        raise ProviderError('Cloud-routed models are not allowed in local acceptance')
    if urlsplit(base).hostname not in ('127.0.0.1','localhost','::1'):
        raise ProviderError('Acceptance requires a loopback endpoint')


def probe(base,model=None,transport=None):
    local_endpoint(base,model)
    out={'evidence_type':'mocked' if transport is not None else 'local_runtime_probe','status':'unavailable','real_inference':'NOT RUN','ollama_binary_present':bool(shutil.which('ollama')),'gpu_utility_present':bool(shutil.which('nvidia-smi')),'model_selected':model,'model_present':False,'tool_capability':False}
    started=time.monotonic()
    try:
        with httpx.Client(trust_env=False,follow_redirects=False,timeout=2,transport=transport) as client:
            def request(method,path,**kwargs):
                with client.stream(method,base.rstrip('/')+path,**kwargs) as response:
                    response.raise_for_status();body=bytearray()
                    for chunk in response.iter_bytes():
                        if time.monotonic()-started>10 or len(body)+len(chunk)>65536:raise ValueError()
                        body.extend(chunk)
                    return json.loads(body)
            v=request('GET','/api/version');tags=request('GET','/api/tags')
            if not isinstance(tags.get('models'),list):raise ValueError()
            out.update(status='available',server_version=v.get('version') if isinstance(v.get('version'),str) and re.fullmatch(r'[0-9A-Za-z.+-]{1,60}',v['version']) else None,installed_model_count=len(tags['models']))
            if model and any(isinstance(m,dict) and model in (m.get('name'),m.get('model')) for m in tags['models']):
                show=request('POST','/api/show',json={'model':model})
                details=show.get('details',{})
                out.update(model_present=True,model_local=not bool(show.get('remote_host') or show.get('remote_model')),tool_capability='tools' in show.get('capabilities',[]))
                for field in ('quantization_level','parameter_size'):
                    value=details.get(field)
                    if isinstance(value,str) and re.fullmatch(r'[A-Za-z0-9_. -]{1,60}',value):out[field]=value
    except Exception:out['reason']='Endpoint unavailable or bounded metadata validation failed; details withheld'
    out['probe_seconds']=round(time.monotonic()-started,3)
    return out


def benchmark(base,model,project_id,samples,concurrency):
    local_endpoint(base,model)
    if not 1<=samples<=3 or concurrency not in (1,2):raise ValueError('Invalid benchmark bounds')
    # Validate selectors BEFORE importing any application configuration/dotenv.
    from sqlalchemy.engine import make_url
    target=make_url(os.environ.get('DATABASE_URL',''))
    if os.getenv('APP_ENV')!='testing' or os.getenv('LLM_ENABLED')!='true' or target.drivername not in ('postgresql','postgresql+psycopg') or target.host not in ('localhost','127.0.0.1','::1') or not (target.database or '').startswith('opendev_test_'):
        raise ValueError('Explicit testing environment and local synthetic database required')
    if any(k not in ('options',) for k in target.query) or target.query.get('options') and not re.fullmatch(r'-csearch_path=[a-z_0-9]+',target.query['options']):raise ValueError('Database overrides rejected')
    from sqlalchemy import create_engine,event
    from sqlalchemy.orm import Session
    from app.services.accountability import read_snapshot
    from app.agent.orchestration import AgentConfig,orchestrate,database_budget
    from app.agent.contracts import AgentQuestion
    from app.agent.tools import EvidenceTools
    from threading import Event
    engine=create_engine(target,connect_args={'hostaddr':'::1' if target.host=='::1' else '127.0.0.1','connect_timeout':3},pool_size=2,max_overflow=0)
    class Measured(OllamaProvider):
        async def chat(self,*args,**kwargs):
            message=await super().chat(*args,**kwargs)
            self.completed_chats+=1
            return message
        async def _request(self,path,payload,timeout):
            value=await super()._request(path,payload,timeout)
            if path=='/api/chat' and isinstance(value,dict):
                self.metrics.append({k:v for k,v in value.items() if k in ('load_duration','eval_count','eval_duration','prompt_eval_count','prompt_eval_duration','total_duration') and isinstance(v,int) and not isinstance(v,bool) and 0<=v<=10**18})
            return value
    def one(case):
        name,question=case;provider=Measured(base,model);provider.metrics=[];provider.completed_chats=0;sql=[0];started=time.monotonic()
        try:
            with Session(engine) as db,read_snapshot(db) as reader:
                conn=reader.connection()
                def count(*args):sql[0]+=1
                event.listen(conn,'before_cursor_execute',count)
                try:
                    config=AgentConfig(timeout_seconds=60,model_timeout=30);cancel=Event()
                    with database_budget(reader,config,cancel):r=asyncio.run(orchestrate(EvidenceTools(reader),AgentQuestion(project_id=project_id,question=question,mode='llm'),provider,config,cancel))
                finally:event.remove(conn,'before_cursor_execute',count)
            return {'case':name,'status':r.answer_status,'actual_mode':r.execution_mode,'latency_ms':round((time.monotonic()-started)*1000,2),'sql_statements':sql[0],'tool_names':r.diagnostics.get('tool_names',[]),'turns':r.diagnostics.get('turn_count',0),'citation_count':len(r.citations),'citation_integrity':bool(r.citations) and all(c in [e.citation for e in r.evidence_used] for c in r.citations),'semantic_grounding':'manual review required','provider_metrics_ns':provider.metrics,'completed_model_messages':provider.completed_chats,'tokens_per_second':[round(m['eval_count']*1e9/m['eval_duration'],2) for m in provider.metrics if m.get('eval_duration',0)>0 and m.get('eval_count',0)>0]}
        except Exception:return {'case':name,'status':'blocked_or_failed','reason':'Application execution failed; details withheld'}
    try:
        with ThreadPoolExecutor(max_workers=concurrency) as pool:results=list(pool.map(one,QUESTIONS*samples))
    finally:engine.dispose()
    return {'evidence_type':'actual_ollama_attempts','model':model,'cases':results,'real_inference':'ran' if any(r.get('completed_model_messages',0)>0 for r in results) else 'NOT RUN or failed before a valid model message','pipeline_checks_passed':all(r.get('actual_mode')=='llm' and r.get('status')=='answered' and r.get('tool_names') and r.get('citation_integrity') for r in results),'first_token_latency':None,'daemon_peak_ram':None,'gpu_peak_vram':None,'benchmark_process_peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'limits':'Nonstreaming requests; no daemon/GPU measurement; source answers/transcripts withheld. Fallbacks are not inference successes.'}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--environment',choices=['local-test'],required=True)
    p.add_argument('--base-url',default=os.getenv('OLLAMA_BASE_URL','http://127.0.0.1:11434'))
    p.add_argument('--model',default=os.getenv('OLLAMA_MODEL'))
    p.add_argument('--execute-inference',action='store_true')
    p.add_argument('--project-id',type=int)
    p.add_argument('--samples',type=int,choices=range(1,4),default=1)
    p.add_argument('--concurrency',type=int,choices=(1,2),default=1)
    args=p.parse_args()
    try:
        result=probe(args.base_url,args.model)
        if args.execute_inference:
            if not args.model or not args.project_id or args.project_id<=0 or not result.get('model_present') or not result.get('model_local') or not result.get('tool_capability'):raise ValueError('Installed local tool-capable model and synthetic project required')
            result['benchmark']=benchmark(args.base_url,args.model,args.project_id,args.samples,args.concurrency)
        print(json.dumps(result,indent=2))
        return 0 if result['status']=='available' and (not args.execute_inference or result['benchmark']['pipeline_checks_passed']) else 2
    except Exception:
        print(json.dumps({'status':'blocked','real_inference':'NOT RUN','reason':'Invalid local acceptance setup; raw details withheld'}));return 2


if __name__=='__main__':raise SystemExit(main())
