import json
import httpx
import pytest
from fastapi import HTTPException
from app.acceptance.providers import run
from app.services.paypal import PayPal
from test_funding import payments,checkout,event,headers
from test_projects import ctx
from test_accountability import ac
from app.models.funding import WebhookEvent


def test_dry_run_never_uses_application_credentials_or_network():
    def denied(request):raise AssertionError('No network allowed')
    env={'PAYPAL_CLIENT_SECRET':'PRIVATE_SENTINEL','SUPABASE_SERVICE_ROLE_KEY':'PRIVATE_SENTINEL','CHECKOUT_ENABLED':'PRIVATE_SENTINEL'}
    r=run(env,transport=httpx.MockTransport(denied))
    assert 'PRIVATE_SENTINEL' not in json.dumps(r)
    assert r['paypal']['status']=='not_run' and r['execution']=='mocked'


@pytest.mark.parametrize('confirm,environment',[(False,'disposable-test'),(True,'production'),(True,'')])
def test_live_confirmation_fails_closed(confirm,environment):
    def denied(request):raise AssertionError('No network allowed')
    r=run({'ACCEPTANCE_ENVIRONMENT':environment},execute=True,confirm=confirm,transport=httpx.MockTransport(denied))
    assert 'blocked' in r


def configured():
    env={'ACCEPTANCE_ENVIRONMENT':'disposable-test'}
    for key in ('PAYPAL_CLIENT_ID','PAYPAL_CLIENT_SECRET','PAYPAL_WEBHOOK_ID','PAYPAL_MERCHANT_ID','SUPABASE_SERVICE_ROLE_KEY'):env['ACCEPTANCE_'+key]='PRIVATE_SENTINEL'
    env['ACCEPTANCE_SUPABASE_PROJECT_REF']='synthetictestref'
    env['ACCEPTANCE_SUPABASE_STORAGE_BUCKET']='opendev-acceptance-fixtures'
    return env


@pytest.mark.parametrize('kind',['success','public','mismatch','invalid-json','oversize','redirect','timeout'])
def test_read_only_probes_are_bounded_redacted_and_labeled(kind):
    calls=[]
    def handler(request):
        calls.append(request)
        assert request.method in ('GET','POST')
        if kind=='timeout':raise httpx.ReadTimeout('PRIVATE_SENTINEL')
        if kind=='redirect':return httpx.Response(302,headers={'Location':'https://attacker.invalid'})
        body=({'access_token':'PRIVATE_SENTINEL'} if request.url.host=='api-m.sandbox.paypal.com' else {'id':'different' if kind=='mismatch' else 'opendev-acceptance-fixtures','public':kind=='public'})
        raw=b'PRIVATE_SENTINEL' if kind=='invalid-json' else b'x'*20000 if kind=='oversize' else json.dumps(body).encode()
        return httpx.Response(200,stream=httpx.ByteStream(raw))
    r=run(configured(),execute=True,confirm=True,transport=httpx.MockTransport(handler))
    assert r['execution']=='mocked' and 'PRIVATE_SENTINEL' not in json.dumps(r)
    assert len(calls)==2 and all(x.url.host in ('api-m.sandbox.paypal.com','synthetictestref.supabase.co') for x in calls)
    assert r['supabase']['status']==('passed' if kind=='success' else 'failed')
    assert r['genuine_webhook_delivery'].startswith('blocked')


def test_malicious_test_host_and_bucket_never_requested():
    env=configured();env['ACCEPTANCE_SUPABASE_PROJECT_REF']='attacker.invalid/path'
    def handler(request):
        assert request.url.host=='api-m.sandbox.paypal.com'
        return httpx.Response(401,stream=httpx.ByteStream(b'{}'))
    r=run(env,execute=True,confirm=True,transport=httpx.MockTransport(handler))
    assert r['supabase']['status'].startswith('blocked')


@pytest.mark.parametrize('links',[None,{},['not-a-link'],[{'rel':'approve','href':'https://www.sandbox.paypal.com:bad/?token=PRIVATE_SENTINEL'}],[{'rel':'approve','href':'https://[malformed'}]])
def test_malformed_approval_is_sanitized(links):
    with pytest.raises(HTTPException) as exc:PayPal().approval({'links':links})
    assert exc.value.status_code==502 and 'PRIVATE_SENTINEL' not in exc.value.detail


@pytest.mark.parametrize('href',['https://[bad','https://api-m.sandbox.paypal.com:bad/v2/payments/captures/CAP1','https://user:PRIVATE_SENTINEL@api-m.sandbox.paypal.com/v2/payments/captures/CAP1','https://api-m.sandbox.paypal.com:444/v2/payments/captures/CAP1'])
def test_bad_refund_links_roll_back_claim(payments,href):
    client,db,*_=payments;c=checkout(payments).json()
    e=event(c,'BAD-LINK','PAYMENT.CAPTURE.REFUNDED');e['resource']['links']=[{'rel':'up','href':href}]
    r=client.post('/api/paypal/webhook',json=e,headers=headers)
    assert r.status_code in (400,502) and 'PRIVATE_SENTINEL' not in r.text
    assert db.get(WebhookEvent,'BAD-LINK') is None


def test_generated_fixture_safety_and_no_overwrite(tmp_path):
    from app.acceptance.fixtures import generate
    root=tmp_path/'fixtures';items=generate(root)
    assert len(items)==9 and all(x['sha256'] for x in items)
    with pytest.raises(FileExistsError):generate(root)
    assert (root/'text.pdf').read_bytes().startswith(b'%PDF-')


@pytest.mark.parametrize('name,mime',[('text.pdf','application/pdf'),('scan.pdf','application/pdf'),('receipt.png','image/png'),('receipt.jpg','image/jpeg')])
def test_generated_receipts_decode_locally(tmp_path,name,mime):
    from app.acceptance.fixtures import generate
    from app.services.receipt.provider import LocalProvider
    root=tmp_path/'fixtures';generate(root)
    receipt=LocalProvider().extract(root/name,mime)
    assert receipt.total_cents.value==1234


def test_network_probe_is_not_live_acceptance():
    def handler(request):return httpx.Response(403,stream=httpx.ByteStream(b''))
    r=run({},probe=True,transport=httpx.MockTransport(handler))
    assert r['network']['paypal']=='blocked_or_provider_rejected'
    assert r['paypal']['status']=='not_run' and r['execution']=='mocked'


def test_capture_webhook_race_keeps_one_capture_and_entitlement(ac,monkeypatch):
    import asyncio
    from concurrent.futures import ThreadPoolExecutor
    from sqlalchemy import select,func
    from sqlalchemy.orm import Session
    from app.models.funding import Contribution,Entitlement
    from app.services import funding
    from test_accountability import contribution
    c=contribution(ac,'created',500,capture=False);c.order_id='ORDER1';ac.db.commit()
    cid=c.id;uid=ac.users[0]
    for key in ('PAYPAL_CLIENT_ID','PAYPAL_CLIENT_SECRET','PAYPAL_WEBHOOK_ID','PAYPAL_MERCHANT_ID'):monkeypatch.setenv(key,'synthetic')
    unit={'custom_id':cid,'payee':{'merchant_id':'synthetic'},'amount':{'currency_code':'USD','value':'5.00'},'payments':{'captures':[{'id':'CAP1'}]}}
    def handler(request):
        if request.url.path=='/v1/oauth2/token':return httpx.Response(200,json={'access_token':'synthetic'})
        if request.url.path.endswith('verify-webhook-signature'):return httpx.Response(200,json={'verification_status':'SUCCESS'})
        if request.url.path=='/v2/payments/captures/CAP1':return httpx.Response(200,json={'id':'CAP1','status':'COMPLETED','amount':unit['amount']})
        assert request.url.path=='/v2/checkout/orders/ORDER1'
        return httpx.Response(200,json={'id':'ORDER1','intent':'CAPTURE','status':'COMPLETED','purchase_units':[unit]})
    monkeypatch.setattr(funding,'paypal',PayPal(httpx.MockTransport(handler)))
    def capture():
        with Session(ac.engine) as db:asyncio.run(funding.capture(db,funding.own(db,cid,uid)))
    def webhook():
        with Session(ac.engine) as db:asyncio.run(funding.webhook(db,event({'order_id':'ORDER1'},'RACE'),headers))
    with ThreadPoolExecutor(max_workers=2) as pool:
        tasks=[pool.submit(capture),pool.submit(webhook)]
        for task in tasks:task.result(timeout=15)
    ac.db.expire_all()
    assert ac.db.get(Contribution,cid).status=='completed'
    assert ac.db.get(Contribution,cid).capture_id=='CAP1'
    assert ac.db.scalar(select(func.count()).select_from(Entitlement))==1
    assert ac.db.scalar(select(func.count()).select_from(WebhookEvent))==1
