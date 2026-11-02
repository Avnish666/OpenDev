from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.user import User
from app.schemas.project import ProjectResponse

router = APIRouter(prefix='/api/me', tags=['My projects'])

@router.get('/projects', response_model=list[ProjectResponse])
def my_projects(db: Session = Depends(get_db), user: User = Depends(get_current_user), limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0)):
    memberships = select(ProjectMember.project_id).where(ProjectMember.user_id == user.id, ProjectMember.role == 'maintainer')
    return db.scalars(select(Project).where((Project.owner_id == user.id) | Project.id.in_(memberships)).order_by(Project.created_at.desc(), Project.id.desc()).limit(limit).offset(offset)).all()
