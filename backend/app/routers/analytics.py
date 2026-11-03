from datetime import date
from typing import Literal
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.routers.expenses import RecordID
from app.schemas.analytics import AnalyticsOverview, ExpenseFilters
from app.services import accountability, analytics

router=APIRouter(prefix='/api/projects',tags=['Public analytics'])

@router.get('/{project_id}/analytics/overview',response_model=AnalyticsOverview)
def overview(project_id:RecordID,limit:int=Query(50,ge=1,le=100),offset:int=Query(0,ge=0,le=10000),
             milestone_offset:int=Query(0,ge=0,le=10000),scope:Literal['public']='public',category:str=Query('',max_length=100),
             evidence:Literal['all','supported','unsupported']='all',date_from:date|None=None,date_to:date|None=None,
             sort:Literal['date_desc','date_asc']='date_desc',db:Session=Depends(get_db)):
    if date_from and date_to and date_from > date_to:
        raise HTTPException(422,'Expense date range is reversed')
    filters=ExpenseFilters(category=category,evidence=evidence,date_from=date_from,date_to=date_to,sort=sort)
    with accountability.read_snapshot(db) as reader:
        return analytics.overview(reader,project_id,limit,offset,filters,milestone_offset)
