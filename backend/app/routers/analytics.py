from typing import Literal
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.routers.expenses import RecordID
from app.schemas.analytics import AnalyticsOverview
from app.services import accountability, analytics

router=APIRouter(prefix='/api/projects',tags=['Public analytics'])

@router.get('/{project_id}/analytics/overview',response_model=AnalyticsOverview)
def overview(project_id:RecordID,limit:int=Query(50,ge=1,le=100),offset:int=Query(0,ge=0,le=10000),
             scope:Literal['public']='public',db:Session=Depends(get_db)):
    with accountability.read_snapshot(db) as reader:
        return analytics.overview(reader,project_id,limit,offset)
