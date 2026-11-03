import pytest
from fastapi import HTTPException
from app.core.config import Settings,settings
from app.core.deployment import validate


@pytest.fixture
def production(monkeypatch):
    for name,value in dict(APP_ENV='production',DATABASE_URL='postgresql+psycopg://synthetic@localhost/opendev_test_preflight',FRONTEND_URL='https://review.invalid',GITHUB_CLIENT_ID='synthetic',GITHUB_CLIENT_SECRET='synthetic',PAYPAL_CLIENT_ID='synthetic',PAYPAL_CLIENT_SECRET='synthetic',PAYPAL_WEBHOOK_ID='synthetic',PAYPAL_MERCHANT_ID='synthetic',SUPABASE_URL='https://synthetic.supabase.co',SUPABASE_STORAGE_BUCKET='private',SUPABASE_SERVICE_ROLE_KEY='synthetic').items():monkeypatch.setenv(name,value)
    for name in ('GITHUB_CALLBACK_URL','FORWARDED_ALLOW_IPS','RECEIPT_PROCESSING_ENABLED','CHECKOUT_ENABLED','LLM_ENABLED'):monkeypatch.delenv(name,raising=False)


def test_restricted_defaults_and_derived_callback(production):
    s=Settings();validate(s)
    assert not s.CHECKOUT_ENABLED and not s.RECEIPT_PROCESSING_ENABLED and not s.LLM_ENABLED
    assert s.GITHUB_CALLBACK_URL=='https://review.invalid/api/auth/github/callback'


@pytest.mark.parametrize('name,value', [('FRONTEND_URL','http://review.invalid'),('FRONTEND_URL','https://review.invalid/'),('GITHUB_CALLBACK_URL','https://other.invalid/callback'),('DATABASE_URL','postgresql://synthetic:PRIVATE_VALUE@remote.invalid/db'),('PAYPAL_CLIENT_SECRET',''),('SUPABASE_URL','http://unsafe.invalid'),('FORWARDED_ALLOW_IPS','*'),('PORT','65536')])
def test_invalid_config_is_redacted(production,monkeypatch,name,value):
    monkeypatch.setenv(name,value)
    with pytest.raises(RuntimeError) as exc:validate(Settings())
    assert name in str(exc.value) and 'PRIVATE_VALUE' not in str(exc.value)


@pytest.mark.parametrize('name',['CHECKOUT_ENABLED','RECEIPT_PROCESSING_ENABLED','LLM_ENABLED'])
def test_flags_are_strict(production,monkeypatch,name):
    monkeypatch.setenv(name,'yes')
    with pytest.raises(RuntimeError):Settings()


def test_disabled_services_have_no_side_effects(monkeypatch):
    from app.core.features import require_receipts,require_checkout
    from app.services import funding,documents
    from app.services.receipt import pipeline
    monkeypatch.setattr(settings,'CHECKOUT_ENABLED',False);monkeypatch.setattr(settings,'RECEIPT_PROCESSING_ENABLED',False)
    for action in [require_receipts,require_checkout,lambda:funding.start(None,None,None,None),lambda:documents.upload(None,None,None,None,None,None,None),lambda:pipeline.process(None,None,None)]:
        with pytest.raises(HTTPException) as error:action()
        assert error.value.status_code==503


def test_client_cannot_override_disabled_llm(ac,monkeypatch):
    from app.agent import providers
    monkeypatch.setattr(settings,'LLM_ENABLED',False)
    def denied(*args,**kwargs):raise AssertionError('Model must not be initialized')
    monkeypatch.setattr(providers.OllamaProvider,'__init__',denied)
    r=ac.client.post(f'/api/projects/{ac.p.id}/agent/query',json={'project_id':ac.p.id,'question':'How much funding is recorded?','mode':'llm'})
    assert r.status_code==200 and r.json()['execution_mode']=='deterministic'

from test_accountability import ac


def test_bad_database_is_redacted_before_engine_import(production,monkeypatch):
    import os,subprocess,sys
    monkeypatch.setenv('DATABASE_URL','postgresql+psycopg://synthetic:PRIVATE_SENTINEL@localhost:invalid/db')
    r=subprocess.run([sys.executable,'-c','import app.main'],env=dict(os.environ),capture_output=True,text=True,timeout=10)
    assert r.returncode!=0 and 'DATABASE_URL' in r.stderr
    assert 'PRIVATE_SENTINEL' not in r.stderr+r.stdout
