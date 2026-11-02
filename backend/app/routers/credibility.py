from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.routers.expenses import RecordID
from app.schemas.credibility import CredibilityProfile, ProjectPage, DeliveryPage
from app.services import accountability, credibility

router=APIRouter(prefix='/api/maintainers/{user_id}',tags=['Public maintainer track record'])


@router.get('/credibility',response_model=CredibilityProfile)
def profile(user_id: RecordID,db: Session=Depends(get_db)):
    with accountability.read_snapshot(db) as reader:
        return credibility.profile(reader,user_id,reader.scalar(select(func.transaction_timestamp())))


@router.get('/projects',response_model=ProjectPage)
def projects(user_id: RecordID,limit: int=Query(20,ge=1,le=100),offset: int=Query(0,ge=0),db: Session=Depends(get_db)):
    with accountability.read_snapshot(db) as reader:
        return credibility.projects(reader,user_id,limit,offset,reader.scalar(select(func.transaction_timestamp())))


@router.get('/delivery-history',response_model=DeliveryPage)
def delivery_history(user_id: RecordID,limit: int=Query(20,ge=1,le=100),offset: int=Query(0,ge=0),db: Session=Depends(get_db)):
    with accountability.read_snapshot(db) as reader:
        return credibility.delivery_history(reader,user_id,limit,offset,reader.scalar(select(func.transaction_timestamp())))
