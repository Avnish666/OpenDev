from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, ConfigDict
from app.core.auth import get_current_user, get_optional_user
from app.core.database import get_db
from app.models.user import User
from app.models.roadmap_dependency import RoadmapDependency as Edge
from app.routers.expenses import RecordID
from app.routers.auth import require_trusted_origin
from app.schemas.roadmap import Versioned
from app.services import roadmap, accountability, roadmap_dependencies as dependencies

router=APIRouter(prefix='/api',tags=['Roadmap dependencies'])


class DependencyCreate(Versioned):
    from_id: int = Field(gt=0,le=9223372036854775807,strict=True)
    to_id: int = Field(gt=0,le=9223372036854775807,strict=True)


class DependencyResponse(BaseModel):
    model_config=ConfigDict(from_attributes=True)
    id: int
    project_id: int
    from_id: int
    to_id: int


class DependencyPage(BaseModel):
    items: list[DependencyResponse]
    total: int
    limit: int
    offset: int


@router.get('/projects/{project_id}/roadmap/dependencies',response_model=DependencyPage)
def listing(project_id: RecordID,limit: int=Query(100,ge=1,le=100),offset: int=Query(0,ge=0),db: Session=Depends(get_db),user: User | None=Depends(get_optional_user)):
    with accountability.read_snapshot(db) as reader:
        roadmap.authorize_project(reader,project_id,user)
        return dict(items=reader.scalars(select(Edge).where(Edge.project_id==project_id).order_by(Edge.id).limit(limit).offset(offset)).all(),
            total=reader.scalar(select(func.count()).select_from(Edge).where(Edge.project_id==project_id)),limit=limit,offset=offset)


@router.post('/projects/{project_id}/roadmap/dependencies',response_model=DependencyResponse,status_code=201,dependencies=[Depends(require_trusted_origin)])
def create(project_id: RecordID,data: DependencyCreate,db: Session=Depends(get_db),user: User=Depends(get_current_user)):
    return dependencies.create(db,project_id,user,data)


@router.delete('/projects/{project_id}/roadmap/dependencies/{dependency_id}',status_code=204,dependencies=[Depends(require_trusted_origin)])
def remove(project_id: RecordID,dependency_id: RecordID,data: Versioned,db: Session=Depends(get_db),user: User=Depends(get_current_user)):
    dependencies.remove(db,project_id,dependency_id,user,data)
