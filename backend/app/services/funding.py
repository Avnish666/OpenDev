from uuid import uuid4
from decimal import Decimal, InvalidOperation
from urllib.parse import urlencode
from fastapi import HTTPException
from sqlalchemy import select, func
from sqlalchemy.dialects.postgresql import insert
from app.models.funding import Contribution, Entitlement, WebhookEvent
from app.models.project import Project
from app.models.reward_tier import RewardTier
from app.core.config import settings
from app.services.paypal import paypal


def own(db, cid, user):
    c = db.scalar(select(Contribution).where(Contribution.id == cid).with_for_update().execution_options(populate_existing=True))
    if not c or c.user_id != user.id: raise HTTPException(404,'Contribution not found')
    return c


def start(db, user, tier_id, key):
    from app.core.features import require_checkout
    require_checkout()
    # Lock the tier before the capacity count and persist the claim before provider I/O.
    tier = db.scalar(select(RewardTier).where(RewardTier.id == tier_id).with_for_update())
    old = db.scalar(select(Contribution).where(Contribution.user_id == user.id, Contribution.checkout_key == key))
    if old:
        if old.tier_id != tier_id: raise HTTPException(409,'Checkout key already used for another tier')
        db.commit()
        return old.id
    if not tier or not tier.active or db.get(Project,tier.project_id).status != 'active': raise HTTPException(404,'Reward unavailable')
    if tier.quantity_limit is not None and db.scalar(select(func.count()).select_from(Contribution).where(Contribution.tier_id == tier.id)) >= tier.quantity_limit:
        raise HTTPException(409,'Reward quantity reserved')
    cid = str(uuid4())
    result = db.execute(insert(Contribution).values(id=cid,user_id=user.id,project_id=tier.project_id,tier_id=tier.id,checkout_key=key,amount_cents=tier.price_cents,currency=tier.currency,reward_snapshot={'name':tier.name,'description':tier.description,'benefits':tier.benefits},status='creating',capture_key=str(uuid4())).on_conflict_do_nothing(index_elements=['user_id','checkout_key']).returning(Contribution.id)).scalar()
    if not result:
        old = db.scalar(select(Contribution).where(Contribution.user_id == user.id, Contribution.checkout_key == key))
        if old.tier_id != tier_id: raise HTTPException(409,'Checkout key already used')
        cid = old.id
    db.commit()
    return cid


async def create_order(db, c):
    if not c.order_id:
        if c.status == 'cancelled': raise HTTPException(409,'Checkout cancelled; start a new checkout')
        from datetime import datetime, timezone, timedelta
        if datetime.now(timezone.utc) - c.created_at.replace(tzinfo=timezone.utc) > timedelta(hours=5):
            raise HTTPException(409,'Uncertain checkout expired; administrator reconciliation required')
        query = urlencode({'contribution':c.id})
        callback = settings.FRONTEND_URL.rstrip('/') + '/?'+query
        result = await paypal.request('POST','/v2/checkout/orders',{
            'intent':'CAPTURE', 'purchase_units':[{'custom_id':c.id,'amount':{'currency_code':c.currency,'value':f'{c.amount_cents // 100}.{c.amount_cents % 100:02d}'},'payee':{'merchant_id':paypal.config('PAYPAL_MERCHANT_ID')}}],
            'payment_source':{'paypal':{'experience_context':{'return_url':callback+'#/funding-return','cancel_url':callback+'#/funding-cancel','user_action':'PAY_NOW'}}}}, c.id)
        c.order_id = paypal.identifier(result.get('id'))
        c.approval_url = paypal.approval(result)
        c.status = 'created'
        db.commit()
    return c


def money_matches(amount, c):
    try:
        return amount.get('currency_code') == c.currency and Decimal(amount['value']) == Decimal(c.amount_cents) / 100
    except (KeyError, TypeError, AttributeError, InvalidOperation): return False


def validate_order(order, c):
    units = order.get('purchase_units')
    if not isinstance(units, list) or len(units) != 1 or not isinstance(units[0],dict):
        raise HTTPException(502,'Unexpected PayPal purchase units')
    unit = units[0]
    if (order.get('id') != c.order_id or order.get('intent') != 'CAPTURE' or
        unit.get('custom_id') != c.id or
        unit.get('payee',{}).get('merchant_id') != paypal.config('PAYPAL_MERCHANT_ID') or
        not money_matches(unit.get('amount',{}),c)):
        raise HTTPException(502,'PayPal order does not match contribution')
    return unit


async def reconcile(db, c, capture_id, terminal=None):
    cap = await paypal.capture_details(capture_id)
    if (cap.get('id') != capture_id or not money_matches(cap.get('amount',{}),c) or
        (c.capture_id and c.capture_id != capture_id)):
        raise HTTPException(502,'PayPal capture does not match contribution')
    # A stored capture ID was already bound to this order and merchant. Terminal
    # signed events must remain usable after the original Orders resource expires.
    if not (terminal and c.capture_id == capture_id):
        unit = validate_order(await paypal.order(c.order_id), c)
        captures = unit.get('payments',{}).get('captures',[])
        if len(captures) != 1 or captures[0].get('id') != capture_id:
            raise HTTPException(502,'PayPal capture does not match order')
    status = cap.get('status')
    if terminal=='refunded' and status not in ('COMPLETED','REFUNDED','PARTIALLY_REFUNDED'):
        raise HTTPException(503,'Refund capture completion not confirmed; retry event')
    entitlement = db.scalar(select(Entitlement).where(Entitlement.contribution_id == c.id))
    c.capture_id = capture_id
    if status=='REFUNDED':
        # PayPal distinguishes REFUNDED from PARTIALLY_REFUNDED: a verified full
        # refund establishes the original gross amount without guessing partials.
        # Individual historical refund IDs remain absent until observed separately.
        c.refund_total_cents=c.amount_cents
    if terminal or status in ('REFUNDED','PARTIALLY_REFUNDED'):
        # A late refund/completion cannot undo an already observed reversal.
        c.status = 'reversed' if c.status=='reversed' else terminal or 'refunded'
        if entitlement: entitlement.status = 'revoked'
    elif c.status not in ('completed','refunded','reversed'):
        if status == 'COMPLETED':
            c.status = 'completed'
            if not entitlement:
                db.add(Entitlement(id=str(uuid4()), contribution_id=c.id, status='granted',fulfillment_note=''))
        elif status == 'PENDING': c.status = 'pending'
        elif status in ('DECLINED','DENIED','FAILED'): c.status = 'denied'
        else: raise HTTPException(502,'Unrecognized PayPal capture status')


async def capture(db, c):
    from app.core.features import require_checkout
    require_checkout()
    if not c.order_id: raise HTTPException(409,'Create order first')
    if c.status in ('completed','refunded','reversed'): return c
    order = await paypal.order(c.order_id)
    unit = validate_order(order, c)
    captures = unit.get('payments',{}).get('captures',[])
    if not captures:
        if c.status == 'cancelled': raise HTTPException(409,'Checkout cancelled')
        if order.get('status') != 'APPROVED': raise HTTPException(409,'Approve checkout at PayPal first')
        # The durable contribution and row lock are the local claim; same provider key on retries.
        result = await paypal.request('POST',f'/v2/checkout/orders/{paypal.identifier(c.order_id)}/capture',{},c.capture_key)
        units = result.get('purchase_units',[])
        captures = units[0].get('payments',{}).get('captures',[]) if len(units)==1 else []
    if len(captures) != 1: raise HTTPException(502,'PayPal capture not yet available; retry')
    await reconcile(db,c,paypal.identifier(captures[0].get('id')))
    db.commit()
    return c


async def webhook(db, event, headers):
    try:
        return await process_webhook(db,event,headers)
    except Exception:
        db.rollback()
        raise


async def process_webhook(db, event, headers):
    await paypal.verify(event, headers)
    event_id, kind = event.get('id'), event.get('event_type')
    if not isinstance(event_id,str) or not event_id or len(event_id)>128 or not isinstance(kind,str) or not kind or len(kind)>128: raise HTTPException(400,'Malformed PayPal event')
    claimed = db.execute(insert(WebhookEvent).values(id=event_id,event_type=kind).on_conflict_do_nothing().returning(WebhookEvent.id)).scalar()
    if not claimed: return {'status':'duplicate'}
    if kind.startswith('PAYMENT.CAPTURE.'):
        resource = event.get('resource',{})
        if not isinstance(resource,dict): raise HTTPException(400,'Malformed capture resource')
        supplementary = resource.get('supplementary_data',{})
        if not isinstance(supplementary,dict) or not isinstance(supplementary.get('related_ids',{}),dict):
            raise HTTPException(400,'Malformed capture references')
        related = supplementary.get('related_ids',{})
        oid = related.get('order_id')
        # Refund resources refer to the original capture through related_ids.
        cap_id = related.get('capture_id') if kind == 'PAYMENT.CAPTURE.REFUNDED' else resource.get('id')
        if kind == 'PAYMENT.CAPTURE.REFUNDED' and not cap_id:
            from urllib.parse import urlparse
            links=resource.get('links',[])
            if not isinstance(links,list):raise HTTPException(400,'Malformed refund references')
            for link in links:
                if not isinstance(link,dict) or not isinstance(link.get('href',''),str):raise HTTPException(400,'Malformed refund references')
                if link.get('rel') == 'up':
                    url = urlparse(link.get('href',''))
                    prefix = '/v2/payments/captures/'
                    if url.scheme == 'https' and url.hostname == 'api-m.sandbox.paypal.com' and url.path.startswith(prefix):
                        cap_id = paypal.identifier(url.path[len(prefix):])
        c = db.scalar(select(Contribution).where(Contribution.order_id == oid).with_for_update().execution_options(populate_existing=True)) if oid else None
        if c is None and cap_id:
            c = db.scalar(select(Contribution).where(Contribution.capture_id == cap_id).with_for_update().execution_options(populate_existing=True))
        if c is None: raise HTTPException(503,'Contribution not yet available; retry event')
        terminal = {'PAYMENT.CAPTURE.REFUNDED':'refunded','PAYMENT.CAPTURE.REVERSED':'reversed'}.get(kind)
        await reconcile(db,c,paypal.identifier(cap_id),terminal=terminal)
        if kind=='PAYMENT.CAPTURE.REFUNDED':
            from app.services.refunds import record
            await record(db,c,resource.get('id'),event_id,paypal)
    db.commit()
    return {'status':'processed'}
