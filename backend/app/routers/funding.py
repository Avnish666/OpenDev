from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.models.funding import Contribution, Entitlement
from app.routers.auth import require_trusted_origin
from app.schemas.funding import Checkout, Fulfill
from app.services import funding
from app.services.project_management import project_for

router = APIRouter(prefix='/api', tags=['Sandbox funding'])

def view(db, c):
    e = db.scalar(select(Entitlement).where(Entitlement.contribution_id == c.id))
    return {'id':c.id,'project_id':c.project_id,'tier_id':c.tier_id,'amount_cents':c.amount_cents,'currency':c.currency,'status':c.status,'order_id':c.order_id,'capture_id':c.capture_id,'approval_url':c.approval_url if c.status=='created' else None,'reward':c.reward_snapshot,'created_at':c.created_at,'entitlement':{'id':e.id,'status':e.status,'fulfillment_note':e.fulfillment_note} if e else None}

@router.post('/funding/orders',dependencies=[Depends(require_trusted_origin)])
async def checkout(data: Checkout,db: Session=Depends(get_db),user: User=Depends(get_current_user)):
    cid = funding.start(db,user,data.tier_id,str(data.checkout_key))
    c = funding.own(db,cid,user)
    await funding.create_order(db,c)
    return view(db,c)

@router.post('/funding/{cid}/capture',dependencies=[Depends(require_trusted_origin)])
async def capture(cid: UUID,db: Session=Depends(get_db),user: User=Depends(get_current_user)):
    c = funding.own(db,str(cid),user)
    await funding.capture(db,c)
    return view(db,c)

@router.post('/funding/{cid}/cancel',dependencies=[Depends(require_trusted_origin)])
def cancel(cid: UUID,db: Session=Depends(get_db),user: User=Depends(get_current_user)):
    c = funding.own(db,str(cid),user)
    if c.status in ('created','creating'): c.status='cancelled'
    db.commit()
    return view(db,c)

@router.get('/me/contributions')
def history(db: Session=Depends(get_db),user: User=Depends(get_current_user),offset: int=Query(0,ge=0),limit: int=Query(20,ge=1,le=100)):
    return [view(db,c) for c in db.scalars(select(Contribution).where(Contribution.user_id==user.id).order_by(Contribution.created_at.desc()).offset(offset).limit(limit))]

@router.get('/projects/{project_id}/fulfillments')
def fulfillments(project_id: int,db: Session=Depends(get_db),user: User=Depends(get_current_user)):
    project_for(db,project_id,user,write=True)
    return [view(db,c) for c in db.scalars(select(Contribution).where(Contribution.project_id==project_id,Contribution.status=='completed'))]

@router.patch('/funding/{cid}/fulfill',dependencies=[Depends(require_trusted_origin)])
def fulfill(cid: UUID,data: Fulfill,db: Session=Depends(get_db),user: User=Depends(get_current_user)):
    c = db.scalar(select(Contribution).where(Contribution.id==str(cid)).with_for_update())
    if not c: raise HTTPException(404,'Contribution not found')
    project_for(db,c.project_id,user,write=True)
    e = db.scalar(select(Entitlement).where(Entitlement.contribution_id==c.id))
    if c.status!='completed' or not e or e.status=='revoked': raise HTTPException(409,'No verified entitlement to fulfill')
    e.status='fulfilled'; e.fulfillment_note=data.note; db.commit()
    return view(db,c)

@router.post('/paypal/webhook')
async def webhook(request: Request,db: Session=Depends(get_db)):
    # Limit bytes while streaming, rather than trusting Content-Length.
    body = bytearray()
    async for chunk in request.stream():
        body.extend(chunk)
        if len(body)>262144: raise HTTPException(413,'Webhook too large')
    import json
    try:
        event=json.loads(body)
        if not isinstance(event,dict): raise ValueError()
    except (ValueError,UnicodeDecodeError): raise HTTPException(400,'Invalid webhook JSON')
    return await funding.webhook(db,event,request.headers)
