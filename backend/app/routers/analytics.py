from app.schemas.dashboard_filters import DashboardDimensions
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
             sort:Literal['date_desc','date_asc']='date_desc',dimensions:DashboardDimensions=Depends(),db:Session=Depends(get_db)):
    if date_from and date_to and date_from > date_to:
        raise HTTPException(422,'Expense date range is reversed')
    if dimensions.planned_from and dimensions.planned_to and dimensions.planned_from>dimensions.planned_to:
        raise HTTPException(422,'Planned deadline range is reversed')
    filters=ExpenseFilters(category=category,evidence=evidence,date_from=date_from,date_to=date_to,sort=sort)
    with accountability.read_snapshot(db) as reader:
        return analytics.overview(reader,project_id,limit,offset,filters,milestone_offset,dimensions)

from fastapi import Request, Response
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from app.services import analytics_exports

@router.get('/{project_id}/analytics/export/{dataset}')
def export_csv(project_id:RecordID,dataset:Literal['expenses','financial','budget','roadmap','github','maintainer-delivery'],request:Request,
               category:str=Query('',max_length=100),evidence:Literal['all','supported','unsupported']='all',
               date_from:date|None=None,date_to:date|None=None,sort:Literal['date_desc','date_asc']='date_desc',scope:Literal['public']='public',
               dimensions:DashboardDimensions=Depends(),db:Session=Depends(get_db)):
    if (date_from and date_to and date_from>date_to) or (dimensions.planned_from and dimensions.planned_to and dimensions.planned_from>dimensions.planned_to):
        raise HTTPException(422,'Date range is reversed')
    analytics_exports.admit(request.client.host if request.client else 'unknown')
    try:
        with accountability.read_snapshot(db) as reader:
            with analytics_exports.budget(reader) as deadline:
                body=analytics_exports.generate(reader,project_id,dataset,ExpenseFilters(category=category,evidence=evidence,date_from=date_from,date_to=date_to,sort=sort),dimensions,deadline)
        return Response(body,media_type='text/csv; charset=utf-8',headers={'Content-Disposition':f'attachment; filename="opendev-project-{project_id}-{dataset}.csv"','Cache-Control':'no-store','X-Content-Type-Options':'nosniff','Referrer-Policy':'no-referrer'})
    except (DBAPIError,TimeoutError):
        raise HTTPException(503,'Export database budget exceeded; narrow filters or retry later') from None
    finally:analytics_exports._slots.release()
