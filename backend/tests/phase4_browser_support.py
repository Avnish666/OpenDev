"""Opt-in local browser bridge for the HTTP release journey; no real providers."""
import os
from pathlib import Path
import socket
import subprocess
import threading
import time
import uvicorn
from app.main import app
from app.core.config import settings


def browser_schedule(ac,monkeypatch,project_id,milestone_id,revised):
    root=Path(__file__).parents[2]
    with socket.socket() as frontend_socket:
        frontend_socket.bind(('127.0.0.1',0));frontend_port=frontend_socket.getsockname()[1]
    origin=f'http://127.0.0.1:{frontend_port}'
    monkeypatch.setattr(settings,'FRONTEND_URL',origin)
    ac.client.headers['Origin']=origin
    listener=socket.socket();listener.bind(('127.0.0.1',0));listener.listen(128)
    backend_port=listener.getsockname()[1]
    server=uvicorn.Server(uvicorn.Config(app,host='127.0.0.1',port=backend_port,log_level='critical',access_log=False))
    thread=threading.Thread(target=server.run,kwargs={'sockets':[listener]},daemon=True);thread.start()
    try:
        for _ in range(100):
            if server.started:break
            time.sleep(.05)
        assert server.started,'Local test API failed to start'
        # Only a synthetic test session is forwarded; no .env or production config.
        env=dict(os.environ,PHASE4_TEST_API=f'http://127.0.0.1:{backend_port}',PHASE4_TEST_PORT=str(frontend_port),
            PHASE4_TEST_PROJECT=str(project_id),PHASE4_TEST_MILESTONE=str(milestone_id),PHASE4_TEST_END=revised,
            PHASE4_TEST_SESSION=ac.client.cookies.get('app_session'))
        subprocess.run(['node','tests/browser-phase4-journey.mjs'],cwd=root/'frontend',env=env,check=True,timeout=100)
    finally:
        server.should_exit=True;thread.join(timeout=10);listener.close()
        assert not thread.is_alive(),'Local test API failed to stop'
