"""Exact completed-refund observations; no refund initiation or historical guesses."""
import re
from fastapi import HTTPException
from sqlalchemy import select,func
from app.models.funding import RefundRecord
from app.services.paypal import BASE_URL


def cents(amount,currency):
    # USD is currently the sole contribution currency. No floats/exponents/rounding.
    if currency!='USD':raise HTTPException(502,'Unsupported refund currency')
    if not isinstance(amount,dict) or amount.get('currency_code') != currency:
        raise HTTPException(502,'Refund currency mismatch')
    value=amount.get('value')
    if not isinstance(value,str) or not re.fullmatch(r'[0-9]{1,17}(?:\.[0-9]{1,2})?',value):
        raise HTTPException(502,'Invalid refund amount')
    whole,_,fraction=value.partition('.')
    result=int(whole)*100+int(fraction.ljust(2,'0') or '0')
    if not 0 < result <= 9223372036854775807:raise HTTPException(502,'Invalid refund amount')
    return result


async def record(db,c,refund_id,event_id,paypal):
    refund_id=paypal.identifier(refund_id)
    body=await paypal.refund_details(refund_id)
    if body.get('id') != refund_id:raise HTTPException(502,'Refund identifier mismatch')
    # Trust only the API resource's exact fixed-host parent link, never follow URLs.
    parent=BASE_URL+'/v2/payments/captures/'+c.capture_id
    links=body.get('links')
    if not isinstance(links,list) or not any(isinstance(x,dict) and x.get('rel')=='up' and x.get('href')==parent for x in links):
        raise HTTPException(502,'Refund capture mismatch')
    if body.get('status') != 'COMPLETED':
        raise HTTPException(503,'Refund completion not yet confirmed; retry event')
    amount=cents(body.get('amount'),c.currency)
    breakdown=body.get('seller_payable_breakdown',{})
    if not isinstance(breakdown,dict):raise HTTPException(502,'Invalid refund breakdown')
    total=cents(breakdown['total_refunded_amount'],c.currency) if 'total_refunded_amount' in breakdown else None
    if amount>c.amount_cents or total is not None and not amount<=total<=c.amount_cents:
        raise HTTPException(502,'Refund total exceeds capture')
    old=db.get(RefundRecord,refund_id)
    if old:
        if (old.contribution_id,old.capture_id,old.currency,old.amount_cents)!=(c.id,c.capture_id,c.currency,amount):
            raise HTTPException(502,'Conflicting refund observation')
        return
    recorded=db.scalar(select(func.coalesce(func.sum(RefundRecord.amount_cents),0)).where(RefundRecord.contribution_id==c.id))
    if recorded+amount>c.amount_cents:raise HTTPException(502,'Refund total exceeds capture')
    # Flush capture/status first; the DB trigger locks the contribution, bounds the
    # unique-refund sum and merges cumulative observations monotonically.
    db.flush()
    db.add(RefundRecord(id=refund_id,contribution_id=c.id,capture_id=c.capture_id,event_id=event_id,
        amount_cents=amount,currency=c.currency,provider_total_cents=total))
    db.flush();db.refresh(c)
