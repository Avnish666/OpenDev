from typing import Literal
from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.routers.expenses import RecordID
from app.routers.accountability import no_cache
from app.schemas.transparency import PublicTransparency, LedgerPage, LedgerEntry
from app.services import accountability, transparency

router = APIRouter(prefix='/api/projects', tags=['Public financial transparency'])


@router.get('/{project_id}/transparency', response_model=PublicTransparency)
def public_transparency(project_id: RecordID, response: Response, db: Session = Depends(get_db)):
    no_cache(response)
    with accountability.read_snapshot(db) as reader:
        return transparency.overview(reader, transparency.public_project(reader, project_id))


@router.get('/{project_id}/ledger', response_model=LedgerPage)
def public_ledger(project_id: RecordID, response: Response, limit: int = Query(20, ge=1, le=100),
                  offset: int = Query(0, ge=0), sort: Literal['date_desc', 'date_asc'] = 'date_desc',
                  q: str = Query('', max_length=200), category: str = Query('', max_length=100),
                  evidence: Literal['all', 'supported', 'unsupported'] = 'all', db: Session = Depends(get_db)):
    no_cache(response)
    with accountability.read_snapshot(db) as reader:
        project = transparency.public_project(reader, project_id)
        return transparency.ledger(reader, project, limit, offset, sort, q.strip(), category, evidence)


@router.get('/{project_id}/ledger/{expense_id}', response_model=LedgerEntry)
def public_ledger_detail(project_id: RecordID, expense_id: RecordID, response: Response, db: Session = Depends(get_db)):
    no_cache(response)
    with accountability.read_snapshot(db) as reader:
        return transparency.detail(reader, transparency.public_project(reader, project_id), expense_id)
