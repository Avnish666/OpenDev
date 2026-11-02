import json
from uuid import uuid4
import httpx
import pytest
from sqlalchemy import select,func
from app.models.funding import Contribution,Entitlement,WebhookEvent
from app.services import funding
from app.services.paypal import PayPal
from test_projects import ctx

@pytest.fixture
def payments(ctx,monkeypatch):
    client,db,p,users,identity=ctx
    p.status='active';db.commit()
    tier=client.post(f'/api/projects/{p.id}/rewards',json={'name':'Supporter','description':'Beta access','price_cents':500,'benefits':[{'title':'Beta'}]}).json()
    for n in ['PAYPAL_CLIENT_ID','PAYPAL_CLIENT_SECRET','PAYPAL_WEBHOOK_ID','PAYPAL_MERCHANT_ID']:monkeypatch.setenv(n,'sandbox-test')
    state={'calls':[],'status':'COMPLETED','captured':False,'valid':True,'amount':'5.00','failure':False}
    def handler(r):
        state['calls'].append(r)
        assert r.url.host=='api-m.sandbox.paypal.com'
        if r.url.path=='/v1/oauth2/token':
            assert r.headers['authorization'].startswith('Basic ')
            assert r.content==b'grant_type=client_credentials'
            return httpx.Response(200,json={'access_token':'test-token'})
        if r.url.path.endswith('verify-webhook-signature'):
            body=json.loads(r.content);assert body['webhook_id']=='sandbox-test' and 'webhook_event' in body
            return httpx.Response(200,json={'verification_status':'SUCCESS' if state['valid'] else 'FAILURE'})
        c=db.scalar(select(Contribution))
        order={'id':'ORDER1','status':'COMPLETED' if state['captured'] else 'APPROVED','purchase_units':[{'custom_id':c.id,'payee':{'merchant_id':'sandbox-test'},'amount':{'currency_code':'USD','value':state['amount']},'payments':{'captures':[{'id':'CAP1'}] if state['captured'] else []}}]}
        if r.url.path=='/v2/checkout/orders' and r.method=='POST':
            body=json.loads(r.content);assert body['purchase_units'][0]['amount']['value']=='5.00';assert r.headers['paypal-request-id']==c.id
            return httpx.Response(201,json={'id':'ORDER1','links':[{'rel':'payer-action','href':'https://www.sandbox.paypal.com/checkoutnow?token=ORDER1'}]})
        if r.url.path.endswith('/capture'):
            assert r.headers['paypal-request-id']==c.capture_key
            if state['failure']:raise httpx.ReadTimeout('test')
            state['captured']=True;order['purchase_units'][0]['payments']['captures']=[{'id':'CAP1'}]
            return httpx.Response(201,json=order)
        if r.url.path=='/v2/checkout/orders/ORDER1':return httpx.Response(200,json=order)
        if r.url.path=='/v2/payments/captures/CAP1':return httpx.Response(200,json={'id':'CAP1','status':state['status'],'final_capture':True,'amount':{'currency_code':'USD','value':state['amount']}})
        raise AssertionError(r.url)
    monkeypatch.setattr(funding,'paypal',PayPal(httpx.MockTransport(handler)))
    return *ctx,tier,state


def checkout(payments,key=None):
    client,db,p,users,identity,tier,state=payments
    return client.post('/api/funding/orders',json={'tier_id':tier['id'],'checkout_key':key or str(uuid4())})


def event(c,event_id='EVENT1',kind='PAYMENT.CAPTURE.COMPLETED'):
    return {'id':event_id,'event_type':kind,'resource':{'id':'CAP1','supplementary_data':{'related_ids':{'order_id':c['order_id']}}}}

headers={n:'test' for n in ['paypal-auth-algo','paypal-cert-url','paypal-transmission-id','paypal-transmission-sig','paypal-transmission-time']}


def test_create_capture_exactly_once_and_history(payments):
    client,db,p,users,identity,tier,state=payments
    key=str(uuid4());r=checkout(payments,key);assert r.status_code==200;c=r.json()
    assert checkout(payments,key).json()['id']==c['id']
    assert len([r for r in state['calls'] if r.method=='POST' and r.url.path=='/v2/checkout/orders'])==1
    for _ in range(2):assert client.post(f"/api/funding/{c['id']}/capture").json()['status']=='completed'
    assert db.scalar(select(func.count()).select_from(Entitlement))==1
    assert client.get('/api/me/contributions').json()[0]['entitlement']['status']=='granted'
    assert client.patch(f"/api/funding/{c['id']}/fulfill",json={'note':'Beta invite sent'}).json()['entitlement']['status']=='fulfilled'
    assert client.get(f'/api/projects/{p.id}/fulfillments').status_code==200

@pytest.mark.parametrize('status,expected',[('PENDING','pending'),('DECLINED','denied')])
def test_noncompleted_no_reward(payments,status,expected):
    client,db,*_=payments;state=payments[-1];state['status']=status;c=checkout(payments).json()
    assert client.post(f"/api/funding/{c['id']}/capture").json()['status']==expected
    assert db.scalar(select(func.count()).select_from(Entitlement))==0
    state['status']='COMPLETED'
    assert client.post('/api/paypal/webhook',json=event(c),headers=headers).status_code==200
    assert db.scalar(select(func.count()).select_from(Entitlement))==1


def test_webhook_signature_duplicates_and_stale_events(payments):
    client,db,*_=payments;state=payments[-1];c=checkout(payments).json();state['captured']=True
    state['valid']=False
    assert client.post('/api/paypal/webhook',json=event(c),headers=headers).status_code==400
    assert db.scalar(select(func.count()).select_from(WebhookEvent))==0
    state['valid']=True
    for _ in range(2):assert client.post('/api/paypal/webhook',json=event(c),headers=headers).status_code==200
    assert db.scalar(select(func.count()).select_from(Entitlement))==1
    state['status']='PENDING'
    assert client.post('/api/paypal/webhook',json=event(c,'EVENT2','PAYMENT.CAPTURE.PENDING'),headers=headers).status_code==200
    assert db.scalar(select(Contribution)).status=='completed'


def test_cancel_authorization_csrf_and_amount_tampering(payments):
    client,db,p,users,identity,tier,state=payments;c=checkout(payments).json()
    assert client.post('/api/funding/orders',json={'tier_id':tier['id'],'checkout_key':str(uuid4()),'amount_cents':1}).status_code==422
    assert client.post(f"/api/funding/{c['id']}/capture",headers={'Origin':'https://evil.test'}).status_code==403
    identity[0]=users[3]
    assert client.post(f"/api/funding/{c['id']}/capture").status_code==404
    assert client.get('/api/me/contributions').json()==[]
    assert client.patch(f"/api/funding/{c['id']}/fulfill",json={'note':'Unauthorized'}).status_code in (403,404)
    identity[0]=users[0]
    assert client.post(f"/api/funding/{c['id']}/cancel").json()['status']=='cancelled'
    assert client.post(f"/api/funding/{c['id']}/capture").status_code==409
    assert db.scalar(select(func.count()).select_from(Entitlement))==0


def test_wrong_amount_no_reward_and_webhook_retry(payments):
    client,db,*_=payments;state=payments[-1];c=checkout(payments).json();state['captured']=True;state['amount']='0.01'
    assert client.post('/api/paypal/webhook',json=event(c),headers=headers).status_code==502
    assert db.scalar(select(func.count()).select_from(WebhookEvent))==0
    assert db.scalar(select(func.count()).select_from(Entitlement))==0
    state['amount']='5.00'
    assert client.post('/api/paypal/webhook',json=event(c),headers=headers).status_code==200


def test_timeout_retry_and_refund_revocation(payments):
    client,db,*_=payments;state=payments[-1];c=checkout(payments).json();state['failure']=True
    assert client.post(f"/api/funding/{c['id']}/capture").status_code==502
    state['failure']=False
    assert client.post(f"/api/funding/{c['id']}/capture").status_code==200
    state['status']='REFUNDED'
    assert client.post('/api/paypal/webhook',json=event(c,'REFUND'),headers=headers).status_code==200
    assert db.scalar(select(Entitlement)).status=='revoked'


def test_quantity_and_snapshot(payments):
    from app.models.reward_tier import RewardTier
    client,db,p,users,identity,tier,state=payments
    t=db.get(RewardTier,tier['id']);t.quantity_limit=1;db.commit();c=checkout(payments).json()
    t.name='Changed';t.price_cents=999;db.commit()
    assert checkout(payments).status_code==409
    assert c['reward']['name']=='Supporter' and c['amount_cents']==500


def test_refund_resource_and_reversal_do_not_regrant(payments):
    client,db,*_=payments;state=payments[-1];c=checkout(payments).json()
    client.post(f"/api/funding/{c['id']}/capture")
    assert client.post('/api/paypal/webhook',json=event(c,'REVERSE','PAYMENT.CAPTURE.REVERSED'),headers=headers).status_code==200
    assert db.scalar(select(Entitlement)).status=='revoked'
    assert client.post('/api/paypal/webhook',json=event(c,'STALE'),headers=headers).status_code==200
    assert db.scalar(select(Entitlement)).status=='revoked'
    state['status']='REFUNDED'
    refund={'id':'REFUND-EVENT','event_type':'PAYMENT.CAPTURE.REFUNDED','resource':{'id':'REFUND1','links':[{'rel':'up','href':'https://api-m.sandbox.paypal.com/v2/payments/captures/CAP1'}]}}
    assert client.post('/api/paypal/webhook',json=refund,headers=headers).status_code==200
    assert db.scalar(select(Contribution)).status=='refunded'


def test_missing_signature_and_no_secrets_in_responses(payments):
    client,db,*_=payments;c=checkout(payments).json()
    assert client.post('/api/paypal/webhook',json=event(c)).status_code==400
    assert 'sandbox-test' not in json.dumps(c)
    assert 'access_token' not in json.dumps(c)
