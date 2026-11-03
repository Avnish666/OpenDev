from pathlib import Path
import subprocess
import pytest
from fastapi import HTTPException
from app.services import documents
from app.services.receipt import provider

def test_decoder_stdout_is_file_bounded_before_parent_read(monkeypatch,tmp_path):
    class Fake:
        returncode=0
        def __init__(self,args,**kwargs):
            assert hasattr(kwargs['stdout'],'fileno')
            assert kwargs['env']=={} and kwargs['start_new_session'] is True
            kwargs['stdout'].write(b'x'*250001);kwargs['stdout'].flush()
        def communicate(self,timeout=None):return None,None
    monkeypatch.setattr(provider.subprocess,'Popen',Fake)
    with pytest.raises(provider.ExtractionError) as exc:provider.LocalProvider().extract(tmp_path/'synthetic','application/pdf')
    assert exc.value.code=='OUTPUT_LIMIT'

def test_decoder_timeout_kills_group_and_drains(monkeypatch,tmp_path):
    killed=[]
    class Fake:
        returncode=0;pid=12345
        def __init__(self,*args,**kwargs):self.calls=0
        def communicate(self,timeout=None):
            self.calls+=1
            if self.calls==1:raise subprocess.TimeoutExpired('synthetic',60)
            return None,None
    monkeypatch.setattr(provider.subprocess,'Popen',Fake);monkeypatch.setattr(provider.os,'killpg',lambda pid,sig:killed.append(pid))
    with pytest.raises(provider.ExtractionError) as exc:provider.LocalProvider().extract(tmp_path/'synthetic','application/pdf')
    assert exc.value.code=='PROCESSING_TIMEOUT' and killed==[12345]

def test_validator_admission_and_error_release(monkeypatch,tmp_path):
    documents._validation_slot.acquire()
    try:
        with pytest.raises(HTTPException) as exc:documents.validate(tmp_path/'missing')
        assert exc.value.status_code==429
    finally:documents._validation_slot.release()
    for _ in range(2):
        with pytest.raises(HTTPException) as exc:documents.validate(tmp_path/'missing')
        assert exc.value.status_code==415

def test_same_origin_static_host_preserves_api_and_blocks_traversal(tmp_path):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from app.core.frontend import mount_frontend
    app=FastAPI()
    @app.get('/api/health')
    def health():return {'status':'ok'}
    site=tmp_path/'site';site.mkdir()
    (site/'index.html').write_text('<html>Community artifact</html>')
    (site/'app.js').write_text('/* synthetic asset */')
    (tmp_path/'credential').write_text('synthetic private fixture outside static root')
    mount_frontend(app,str(site))
    with TestClient(app) as client:
        assert client.get('/api/health').json()=={'status':'ok'}
        assert 'Community artifact' in client.get('/').text
        assert client.get('/app.js').text=='/* synthetic asset */'
        assert client.get('/missing-asset').status_code==404
        assert client.get('/%2e%2e/credential').status_code==404
    with pytest.raises(RuntimeError):mount_frontend(FastAPI(),tmp_path/'missing')
