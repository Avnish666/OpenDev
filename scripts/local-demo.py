"""Run the unchanged application on loopback with all three restricted features off."""
from pathlib import Path
import argparse
import os
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
from app.acceptance.demo import local_database
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--port',type=int,default=8000)
a=p.parse_args()
try:
    local_database()
    if not 1024<=a.port<=65535:raise ValueError()
    if os.getenv('FRONTEND_URL') not in ('http://127.0.0.1:5173','http://localhost:5173'):raise ValueError()
except Exception:
    raise SystemExit('Blocked: explicit synthetic testing configuration, local DB and loopback frontend required') from None
# Never load ambient application .env provider credentials in this demo process.
os.environ["PYTHON_DOTENV_DISABLED"]="1"
# No monkeypatches, dependency overrides, session injection or special auth routes.
import uvicorn
uvicorn.run('app.main:app',host='127.0.0.1',port=a.port,access_log=False,timeout_graceful_shutdown=5)
