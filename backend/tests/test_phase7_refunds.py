"""Authoritative Sandbox refund replay/amount/DB-integrity regressions."""
import pytest
from sqlalchemy import select,func,text,insert
from sqlalchemy.exc import DBAPIError
from app.models.funding import Contribution,Entitlement,WebhookEvent,RefundRecord
from test_funding import payments,checkout,event,headers
from test_projects import ctx
from test_accountability import ac,contribution


def completed(payments):
    client=payments[0];c=checkout(payments).json()
    assert client.post(f"/api/funding/{c['id']}/capture").status_code==200
    return c


def refund_body(rid,amount='1.00',total='1.00'):
    return dict(id=rid,status='COMPLETED',amount=dict(currency_code='USD',value=amount),
        seller_payable_breakdown={} if total is None else {'total_refunded_amount':dict(currency_code='USD',value=total)},
        links=[dict(rel='up',href='https://api-m.sandbox.paypal.com/v2/payments/captures/CAP1')])


def send(payments,c,rid='R1',amount='1.00',total='1.00',eid=None,body=None):
    payments[-1]['refund_override']=body or refund_body(rid,amount,total)
    e=event(c,eid or 'EVENT-'+rid,'PAYMENT.CAPTURE.REFUNDED')
    e['resource']['id']=rid;e['resource']['supplementary_data']['related_ids']['capture_id']='CAP1'
    return payments[0].post('/api/paypal/webhook',json=e,headers=headers)


def snapshot(payments):
    from app.services.accountability import snapshot
    return snapshot(payments[1],payments[2],None)


def test_multiple_partial_refunds_duplicate_ids_and_out_of_order(payments):
    client,db,*_=payments;c=completed(payments)
    assert send(payments,c,'R2','2.00','3.00').status_code==200
    assert send(payments,c,'R2','2.00','3.00').json()['status']=='duplicate'
    assert send(payments,c,'R2','2.00','3.00',eid='DUPLICATE-ID-NEW-EVENT').status_code==200
    assert db.scalar(select(func.count()).select_from(RefundRecord))==1
    assert send(payments,c,'R1','1.00','1.00').status_code==200
    assert db.get(Contribution,c['id']).refund_total_cents==300
    s=snapshot(payments)
    assert (s['exact_refund_total_cents'],s['refund_excluded_cents'],s['net_recorded_funding_cents'])==(300,300,200)
    legacy=client.get(f'/api/projects/{payments[2].id}/financial-summary').json()
    assert legacy['completed_funding_cents']==200 and legacy['excluded_refunded_or_reversed_cents']==300
    assert db.scalar(select(Entitlement)).status=='revoked'
    assert send(payments,c,'R3','2.00','5.00').status_code==200
    assert snapshot(payments)['net_recorded_funding_cents']==0
    assert client.post('/api/paypal/webhook',json=event(c,'LATE-COMPLETION'),headers=headers).status_code==200
    assert db.scalar(select(Entitlement)).status=='revoked'
    assert db.scalar(select(func.count()).select_from(RefundRecord))==3


def test_refund_before_completion_never_grants_reward(payments):
    client,db,*_=payments;c=checkout(payments).json();payments[-1]['captured']=True
    assert send(payments,c).status_code==200
    assert snapshot(payments)['net_recorded_funding_cents']==400
    assert client.post(f"/api/funding/{c['id']}/capture").json()['refund_total_cents']==100
    assert db.scalar(select(func.count()).select_from(Entitlement))==0


@pytest.mark.parametrize('status',['PENDING','DECLINED','FAILED'])
def test_uncompleted_capture_remains_excluded(payments,status):
    client,db,*_=payments;payments[-1]['status']=status;c=completed(payments)
    assert send(payments,c).status_code==503
    assert db.scalar(select(func.count()).select_from(RefundRecord))==0
    assert db.scalar(select(func.count()).select_from(Entitlement))==0
    assert snapshot(payments)['net_recorded_funding_cents']==0
    assert db.get(WebhookEvent,'EVENT-R1') is None


@pytest.mark.parametrize('field,value',[
    ('amount','-1.00'),('amount','1.001'),('amount','1e0'),('amount','NaN'),('amount',1.0),
    ('amount','0.00'),('amount','6.00'),('total','6.00'),('total','0.50'),
    ('currency','EUR'),('parent','https://attacker.invalid/captures/CAP1'),('id','OTHER')])
def test_invalid_authoritative_refund_rolls_back_event(payments,field,value):
    client,db,*_=payments;c=completed(payments);body=refund_body('R1')
    if field=='amount':body['amount']['value']=value
    elif field=='total':body['seller_payable_breakdown']['total_refunded_amount']['value']=value
    elif field=='currency':body['amount']['currency_code']=value
    elif field=='parent':body['links'][0]['href']=value
    else:body['id']=value
    assert send(payments,c,body=body).status_code==502
    assert db.get(WebhookEvent,'EVENT-R1') is None
    assert db.scalar(select(func.count()).select_from(RefundRecord))==0
    assert db.get(Contribution,c['id']).status=='completed'
    assert db.scalar(select(Entitlement)).status=='granted'


def test_pending_refund_retries_same_event_and_conflicting_id_rejected(payments):
    client,db,*_=payments;c=completed(payments);body=refund_body('R1');body['status']='PENDING'
    assert send(payments,c,body=body).status_code==503
    assert send(payments,c).status_code==200
    assert send(payments,c,amount='2.00',total='2.00',eid='CONFLICT').status_code==502
    assert db.get(WebhookEvent,'CONFLICT') is None
    assert db.get(Contribution,c['id']).refund_total_cents==100


def test_unknown_legacy_aggregate_is_not_invented(payments):
    client,db,*_=payments;c=completed(payments)
    assert send(payments,c,amount='2.00',total=None).status_code==200
    s=snapshot(payments)
    assert s['exact_refund_total_cents'] is None and s['net_recorded_funding_cents']==0
    assert db.get(Contribution,c['id']).refund_total_cents is None
    assert db.get(RefundRecord,'R1').amount_cents==200
    assert send(payments,c,'R2','1.00','3.00').status_code==200
    assert snapshot(payments)['net_recorded_funding_cents']==200


def test_reversal_and_late_refund_never_double_subtract_or_regrant(payments):
    client,db,*_=payments;c=completed(payments)
    assert send(payments,c).status_code==200
    assert client.post('/api/paypal/webhook',json=event(c,'REVERSE','PAYMENT.CAPTURE.REVERSED'),headers=headers).status_code==200
    assert send(payments,c,'R2','1.00','2.00').status_code==200
    s=snapshot(payments)
    assert s['refund_excluded_cents']==0 and s['reversal_excluded_cents']==500 and s['net_recorded_funding_cents']==0
    assert db.get(Contribution,c['id']).status=='reversed' and db.scalar(select(Entitlement)).status=='revoked'


def test_sum_bound_and_database_immutability(payments):
    client,db,*_=payments;c=completed(payments)
    assert send(payments,c,'R1','3.00','3.00').status_code==200
    assert send(payments,c,'R2','3.00','3.00').status_code==502
    for sql in ["UPDATE paypal_refunds SET amount_cents=1", "DELETE FROM paypal_refunds",
                "UPDATE contributions SET refund_total_cents=0", "UPDATE contributions SET capture_id='OTHER'",
                "UPDATE contributions SET refund_total_cents=600"]:
        with pytest.raises(DBAPIError):
            with db.begin_nested():db.execute(text(sql))
    assert db.get(RefundRecord,'R1').amount_cents==300
    assert db.get(Contribution,c['id']).refund_total_cents==300
    with pytest.raises(DBAPIError):
        with db.begin_nested():
            db.execute(insert(RefundRecord).values(id='DIRECT-OVERFLOW',contribution_id=c['id'],capture_id='CAP1',
                event_id='EVENT-R1',amount_cents=300,currency='USD',provider_total_cents=300))


def test_known_refund_public_api_analytics_csv_and_agent_parity(ac):
    c=contribution(ac,'refunded',500)
    # Synthetic authoritative snapshot; replay/ledger validation is covered above.
    c.refund_total_cents=300;ac.db.commit()
    for path,key in [(f'/api/projects/{ac.p.id}/transparency','financial_summary'),
                     (f'/api/projects/{ac.p.id}/analytics/overview','financial')]:
        r=ac.client.get(path);assert r.status_code==200,r.text
        s=r.json()[key]
        assert s['net_recorded_funding_cents']==200 and s['exact_refund_total_cents']==300
    response=ac.client.get(f'/api/projects/{ac.p.id}/analytics/export/financial')
    assert response.status_code==200 and '200' in response.text
    answer=ac.client.post(f'/api/projects/{ac.p.id}/agent/query',json={'project_id':ac.p.id,'question':'How much has been refunded?','mode':'deterministic'})
    assert answer.status_code==200,answer.text
    assert '300 USD minor units' in answer.json()['answer']
    assert 'not a live bank balance' in answer.json()['answer']


def test_concurrent_refund_events_serialize_and_deduplicate(ac,monkeypatch):
    import asyncio
    from concurrent.futures import ThreadPoolExecutor
    from uuid import uuid4
    import httpx
    from sqlalchemy.orm import Session
    from app.services import funding
    from app.services.paypal import PayPal
    c=contribution(ac,'completed',500);c.capture_id='CAP1';c.order_id='ORDER1'
    ac.db.add(Entitlement(id=str(uuid4()),contribution_id=c.id,status='granted',fulfillment_note=''))
    ac.db.commit()
    for name in ['PAYPAL_CLIENT_ID','PAYPAL_CLIENT_SECRET','PAYPAL_WEBHOOK_ID']:monkeypatch.setenv(name,'synthetic-test')
    def handler(request):
        path=request.url.path
        if path=='/v1/oauth2/token':return httpx.Response(200,json={'access_token':'synthetic'})
        if path.endswith('verify-webhook-signature'):return httpx.Response(200,json={'verification_status':'SUCCESS'})
        if path=='/v2/payments/captures/CAP1':return httpx.Response(200,json={'id':'CAP1','status':'COMPLETED','amount':{'currency_code':'USD','value':'5.00'}})
        rid=path.rsplit('/',1)[1]
        assert rid in ('R1','R2')
        return httpx.Response(200,json=refund_body(rid,'1.00' if rid=='R1' else '0.50','1.00' if rid=='R1' else '1.50'))
    monkeypatch.setattr(funding,'paypal',PayPal(httpx.MockTransport(handler)))
    def process(pair):
        rid,eid=pair;e=event({'order_id':'ORDER1'},eid,'PAYMENT.CAPTURE.REFUNDED')
        e['resource']['id']=rid;e['resource']['supplementary_data']['related_ids']['capture_id']='CAP1'
        with Session(ac.engine) as db:return asyncio.run(funding.webhook(db,e,headers))['status']
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(process,[('R1','E1'),('R1','E1'),('R2','E2'),('R1','E3')]))
    ac.db.expire_all()
    assert results.count('duplicate')==1
    assert ac.db.scalar(select(func.count()).select_from(RefundRecord))==2
    assert ac.db.get(Contribution,c.id).refund_total_cents==150
    assert ac.db.scalar(select(Entitlement)).status=='revoked'


def test_late_full_refund_capture_status_overrides_stale_partial_total(payments):
    client,db,*_=payments;c=completed(payments)
    assert send(payments,c).status_code==200
    payments[-1]['status']='REFUNDED'
    assert client.post('/api/paypal/webhook',json=event(c,'FULL-STATUS'),headers=headers).status_code==200
    s=snapshot(payments)
    assert s['net_recorded_funding_cents']==0 and s['exact_refund_total_cents']==500
    assert db.get(Contribution,c['id']).refund_total_cents==500
    assert db.scalar(select(func.count()).select_from(RefundRecord))==1
    assert db.scalar(select(Entitlement)).status=='revoked'
