"""Read-only local Git/config heuristic audit. Prints identifiers/categories, never values.
No credential validation, network access, working .env/private-file read or history rewrite.
"""
import json,re,subprocess,argparse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('--working-only',action='store_true',help='Do not read any historical blobs; scan non-ignored safe working files only')
args=parser.parse_args()
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT,stderr=subprocess.DEVNULL)
patterns={
 'database_password_url':re.compile(r'postgres(?:ql)?(?:\+\w+)?://[^\s/:\'\"]+:[^\s@\'\"]+@[^\s/\'\"]+',re.I),
 'provider_token':re.compile(r'(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{30,}|eyJ[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{15,})')}
for key,category in [('GITHUB_CLIENT_SECRET','github_oauth_client_secret'),('PAYPAL_CLIENT_SECRET','paypal_client_secret'),('SUPABASE_SERVICE_ROLE_KEY','storage_service_role'),('VITE_AG_STUDIO_LICENSE_KEY','studio_license'),('SESSION_SECRET','session_secret')]:
    patterns[category]=re.compile(re.escape(key)+r"\s*[:=]\s*(?:['\"]([^'\"\r\n]{8,})['\"]|([A-Za-z0-9_./+:-]{8,}))[ \t]*(?:$|[,}#])",re.M)
placeholder=re.compile(r'localhost|127\.0\.0\.1|example|placeholder|replace|change.me|your_|dummy|synthetic|test-|\$\{|<',re.I)
seen=set();findings=[];skipped=0
commits=[] if args.working_only else git('rev-list','--all').decode().splitlines()
for commit in commits:
 for entry in git('ls-tree','-rz',commit).split(b'\0'):
  if not entry:continue
  meta,path=entry.split(b'\t',1);parts=meta.split();kind,blob=parts[1:3]
  if kind!=b'blob' or (blob,path) in seen:continue
  seen.add((blob,path));name=path.decode('utf8','replace')
  size=int(git('cat-file','-s',blob.decode()))
  if size>1024*1024:skipped+=1;continue
  raw=git('cat-file','blob',blob.decode())
  text=raw.decode('utf-16' if raw[:2] in (b'\xff\xfe',b'\xfe\xff') else 'utf8','ignore')
  for category,pattern in patterns.items():
   if any(not placeholder.search(m.group(0)) for m in pattern.finditer(text)):
    findings.append(dict(path=name,category=category,commit=commit,blob=blob.decode(),status='potential exposure; requires owner assessment',fixture_area='/tests/' in name or name.startswith('backend/tests/')))
working_findings=[];working_scanned=0
for raw_path in set(git('ls-files','-c','-o','--exclude-standard','-z').split(b'\0')):
 if not raw_path:continue
 name=raw_path.decode('utf8','replace');path=ROOT/name
 # Never follow a symlink to a private file, nor inspect working credential files.
 if path.is_symlink() or not path.is_file() or path.stat().st_size>1024*1024:continue
 if (path.name.startswith('.env') and path.name!='.env.example') or path.suffix.lower() in ('.pem','.key','.p12') or 'credentials' in path.name.lower():continue
 raw=path.read_bytes();working_scanned+=1
 text=raw.decode('utf-16' if raw[:2] in (b'\xff\xfe',b'\xfe\xff') else 'utf8','ignore')
 for category,pattern in patterns.items():
  if any(not placeholder.search(m.group(0)) for m in pattern.finditer(text)):
   working_findings.append(dict(path=name,category=category,status='potential exposure; requires owner assessment'))
print(json.dumps(dict(scope=('Working-only; history not read. ' if args.working_only else 'Locally available reachable Git blobs and ')+ 'non-ignored source files, <=1MiB; working credential files and symlinks excluded. No values emitted or credentials tested.',shallow=git('rev-parse','--is-shallow-repository').decode().strip(),commits=len(commits),unique_blob_paths=len(seen),oversize_skipped=skipped,findings=findings,working_files_scanned=working_scanned,working_findings=working_findings),indent=2))
