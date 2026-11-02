
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectResponse
from app.services.github_repository import verify_repository_ownership
from app.services.project_service import create_project

# Import the origin guard from your existing auth router.
from app.routers.auth import require_trusted_origin

router = APIRouter(
    prefix="/api/projects",
    tags=["Projects"],
)


@router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_trusted_origin)],
)
async def create_project_endpoint(
    data: ProjectCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if user.github_id is None:
        raise HTTPException(
            status_code=403,
            detail="A GitHub account is required",
        )

    repo = await verify_repository_ownership(
        repo_name=data.github_repo,
        github_user_id=user.github_id,
    )

    return create_project(
        db=db,
        owner_id=user.id,
        repo=repo,
        data=data,
    )


@router.get("", response_model=list[ProjectResponse])
def list_projects(
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    if not 1 <= limit <= 100 or offset < 0:
        raise HTTPException(
            status_code=422,
            detail="Invalid pagination values",
        )

    stmt = (
        select(Project)
        .where(Project.status == "active")
        .order_by(Project.created_at.desc(), Project.id.desc())
        .offset(offset)
        .limit(limit)
    )

    return db.scalars(stmt).all()


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
):
    project = db.get(Project, project_id)

    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    # Draft projects must not be public.
    if project.status != "active":
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    return project
