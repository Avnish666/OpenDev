from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.core.auth import get_current_user, get_optional_user
from app.core.database import get_db
from app.models.user import User
from app.models.roadmap import ProjectRoadmapMilestone as Milestone
from app.routers.auth import require_trusted_origin
from app.routers.expenses import RecordID
from app.schemas.roadmap import Commitment, RoadmapPatch, StatusChange, EvidenceCreate, Versioned, MilestoneResponse, RoadmapPage, HistoryResponse
from app.services import roadmap, accountability

router=APIRouter(prefix='/api',tags=['Project roadmap'])


@router.post('/projects/{project_id}/roadmap',response_model=MilestoneResponse,status_code=201,dependencies=[Depends(require_trusted_origin)])
def create(project_id: RecordID,data: Commitment,db: Session=Depends(get_db),user: User=Depends(get_current_user)):
    return roadmap.view(db,roadmap.create(db,project_id,user,data),user)


@router.get('/projects/{project_id}/roadmap',response_model=RoadmapPage)
def listing(project_id: RecordID,limit: int=Query(20,ge=1,le=100),offset: int=Query(0,ge=0),db: Session=Depends(get_db),user: User | None=Depends(get_optional_user)):
    with accountability.read_snapshot(db) as reader:
        roadmap.authorize_project(reader,project_id,user)
        rows=reader.scalars(select(Milestone).where(Milestone.project_id==project_id).order_by(Milestone.display_order,Milestone.id).limit(limit).offset(offset)).all()
        return dict(items=[roadmap.view(reader,row,user) for row in rows],total=reader.scalar(select(func.count()).select_from(Milestone).where(Milestone.project_id==project_id)),limit=limit,offset=offset)


@router.patch('/roadmap/{milestone_id}',response_model=MilestoneResponse,dependencies=[Depends(require_trusted_origin)])
def edit(milestone_id: RecordID,data: RoadmapPatch,db: Session=Depends(get_db),user: User=Depends(get_current_user)):
    return roadmap.view(db,roadmap.edit(db,milestone_id,user,data),user)


@router.post('/roadmap/{milestone_id}/evidence',response_model=MilestoneResponse,dependencies=[Depends(require_trusted_origin)])
def link(milestone_id: RecordID,data: EvidenceCreate,db: Session=Depends(get_db),user: User=Depends(get_current_user)):
    return roadmap.view(db,roadmap.link(db,milestone_id,user,data),user)


@router.delete('/roadmap/{milestone_id}/evidence/{evidence_id}',response_model=MilestoneResponse,dependencies=[Depends(require_trusted_origin)])
def unlink(milestone_id: RecordID,evidence_id: UUID,data: Versioned,db: Session=Depends(get_db),user: User=Depends(get_current_user)):
    return roadmap.view(db,roadmap.unlink(db,milestone_id,str(evidence_id),user,data),user)


@router.post('/roadmap/{milestone_id}/status',response_model=MilestoneResponse,dependencies=[Depends(require_trusted_origin)])
def status(milestone_id: RecordID,data: StatusChange,db: Session=Depends(get_db),user: User=Depends(get_current_user)):
    return roadmap.view(db,roadmap.change_status(db,milestone_id,user,data),user)


@router.get('/roadmap/{milestone_id}/history',response_model=list[HistoryResponse])
def history(milestone_id: RecordID,limit: int=Query(20,ge=1,le=100),offset: int=Query(0,ge=0),db: Session=Depends(get_db),user: User | None=Depends(get_optional_user)):
    with accountability.read_snapshot(db) as reader:
        return roadmap.history(reader,roadmap.get(reader,milestone_id,user),user,limit,offset)
