"""Local-only read-only load sample. Requires a fresh named test DB; never drops data."""
from pathlib import Path
import argparse,re,subprocess,json,time,urllib.request,concurrent.futures,statistics
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--image',default='opendev-review:phase7-step3')
parser.add_argument('--database',default='opendev_test_phase7_step3_metrics')
parser.add_argument('--output',type=Path,default=Path(__file__).resolve().parents[1]/'docs/phase7-step3-local-capacity.json')
args=parser.parse_args()
if not re.fullmatch(r'opendev_test_[a-z0-9_]+',args.database):parser.error('Fresh synthetic test database name required')
D=['docker','--host=unix:///var/run/docker.sock']
def run(*args):return subprocess.check_output(D+list(args),text=True).strip()
run('exec','opendev-phase7-postgres','createdb','-U','opendev',args.database)
ip=run('inspect','-f','{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}','opendev-phase7-postgres')
start=time.monotonic()
cid=run('run','-d','--memory=512m','--cpus=1','--read-only','--tmpfs','/tmp:rw,noexec,nosuid,nodev,size=64m','--cap-drop=ALL','--security-opt','no-new-privileges','-p','127.0.0.1:18084:10000','-e','APP_ENV=testing','-e',f'DATABASE_URL=postgresql+psycopg://opendev@{ip}:5432/{args.database}','-e','RECEIPT_PROCESSING_ENABLED=false','-e','CHECKOUT_ENABLED=false','-e','LLM_ENABLED=false',args.image)
try:
 for _ in range(80):
  try:urllib.request.urlopen('http://127.0.0.1:18084/api/health',timeout=1).read();break
  except OSError:time.sleep(.1)
 else:raise RuntimeError('Local image did not start')
 startup=time.monotonic()-start
 def request(path):
  t=time.monotonic()
  with urllib.request.urlopen('http://127.0.0.1:18084'+path,timeout=10) as r:body=r.read();return r.status,round((time.monotonic()-t)*1000,2),len(body)
 root=request('/')
 with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:results=list(ex.map(request,['/api/db-health']*20))
 stats=json.loads(run('stats','--no-stream','--format','{{json .}}',cid))
 connections=run('exec','opendev-phase7-postgres','psql','-U','opendev','-d','postgres','-Atc',f"SELECT count(*) FROM pg_stat_activity WHERE datname='{args.database}'")
 out=dict(scope='Local testing-mode DB/static concurrency sample; not hosted production/HTTPS or worst-case OCR capacity',startup_seconds=round(startup,2),static_root=root,concurrency=8,requests=20,statuses=[r[0] for r in results],median_ms=statistics.median(r[1] for r in results),max_ms=max(r[1] for r in results),retained_db_connections=int(connections),docker_cpu_sample=stats['CPUPerc'],docker_memory_sample=stats['MemUsage'])
finally:
 stop=time.monotonic();run('stop','-t','5',cid);duration=round(time.monotonic()-stop,2);exit_code=run('inspect','-f','{{.State.ExitCode}}',cid);run('rm',cid)
out.update(image=args.image,shutdown_seconds=duration,exit_code=int(exit_code));args.output.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
