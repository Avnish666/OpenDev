import asyncio,json
import httpx
import pytest
from app.acceptance.ollama import probe,local_endpoint,benchmark
from app.agent.providers import OllamaProvider,ProviderError,GenerationSettings


@pytest.mark.parametrize('base',['http://public.invalid:11434','http://169.254.169.254','http://localhost:bad','http://[broken','http://user:PRIVATE@localhost:11434','http://localhost:11434/path'])
def test_local_acceptance_rejects_unsafe_endpoints(base):
    with pytest.raises(ProviderError):local_endpoint(base,'qwen3:4b')


@pytest.mark.parametrize('model',[None,'',42,'qwen3\nSECRET',' model'])
def test_provider_bad_model_is_sanitized(model):
    with pytest.raises(ProviderError) as e:OllamaProvider('http://127.0.0.1:11434',model)
    assert 'SECRET' not in str(e.value)


@pytest.mark.parametrize('kind',['ready','missing','no-tools','timeout','oversized','redirect','malformed'])
def test_detection_is_bounded_and_not_inference(kind):
    calls=[]
    def handle(r):
        calls.append(r)
        assert r.url.path in ('/api/version','/api/tags','/api/show')
        if kind=='timeout':raise httpx.ReadTimeout('PRIVATE_ERROR')
        if kind=='redirect':return httpx.Response(302,headers={'location':'https://attacker.invalid'})
        if kind=='oversized':return httpx.Response(200,content=b'x'*70000)
        if kind=='malformed':return httpx.Response(200,content=b'PRIVATE_ERROR')
        body={'version':'0.12.0'} if r.url.path=='/api/version' else {'models':[] if kind=='missing' else [{'name':'qwen3:4b'}]} if r.url.path=='/api/tags' else {'capabilities':[] if kind=='no-tools' else ['tools'],'details':{'quantization_level':'Q4_K_M'}}
        return httpx.Response(200,json=body)
    r=probe('http://127.0.0.1:11434','qwen3:4b',httpx.MockTransport(handle))
    assert r['evidence_type']=='mocked' and r['real_inference']=='NOT RUN'
    assert 'PRIVATE_ERROR' not in json.dumps(r)
    assert len(calls)<=3
    if kind=='ready':assert r['model_present'] and r['tool_capability']
    if kind=='missing':assert not r['model_present']
    if kind=='no-tools':assert not r['tool_capability']


@pytest.mark.parametrize('message',[{'content':'no role'},{'role':'user','content':'PRIVATE_ERROR'},['not-a-message']])
def test_provider_requires_explicit_assistant_role(message):
    p=OllamaProvider('http://127.0.0.1:11434','qwen3:4b',httpx.MockTransport(lambda r:httpx.Response(200,json={'done':True,'message':message})))
    with pytest.raises(ProviderError):asyncio.run(p.chat([],[],GenerationSettings(),1))


def test_benchmark_rejects_database_overrides_before_import(monkeypatch):
    monkeypatch.setenv('APP_ENV','testing');monkeypatch.setenv('LLM_ENABLED','true')
    monkeypatch.setenv('DATABASE_URL','postgresql+psycopg://u@localhost/opendev_test_sample?host=production.invalid')
    with pytest.raises(ValueError):benchmark('http://localhost:11434','qwen3:4b',1,1,1)
