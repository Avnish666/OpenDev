from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.routers.expenses import RecordID
from app.schemas.progress import ProgressSummary
from app.services import accountability, progress

router=APIRouter(prefix='/api/projects',tags=['Public project progress'])


@router.get('/{project_id}/progress-summary',response_model=ProgressSummary)
def summary(project_id: RecordID,db: Session=Depends(get_db)):
    with accountability.read_snapshot(db) as reader:
        return progress.summary(reader,project_id)
