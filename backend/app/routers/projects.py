
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.auth import get_current_user, get_optional_user
from app.core.database import get_db
from app.models.user import User
from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectResponse
from app.services.github_repository import verify_repository_ownership
from app.services.project_service import create_project

# Import the origin guard from your existing auth router.
from app.routers.auth import require_trusted_origin

from app.schemas.project import ProjectDetail, ProjectPatch
from app.schemas.reward import RewardCreate, RewardPatch, RewardResponse
from app.models.reward_tier import RewardTier
from app.services import project_management as management

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


@router.get("/{project_id}", response_model=ProjectDetail)
def get_project(project_id: int, db: Session = Depends(get_db), user: User | None = Depends(get_optional_user)):
    return management.detail(db, management.project_for(db, project_id, user), user)


@router.patch("/{project_id}", response_model=ProjectDetail, dependencies=[Depends(require_trusted_origin)])
def edit_project(project_id: int, data: ProjectPatch, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    project = management.project_for(db, project_id, user, write=True)
    management.update_project(db, project, data)
    return management.detail(db, project, user)


@router.post("/{project_id}/publish", response_model=ProjectDetail, dependencies=[Depends(require_trusted_origin)])
async def publish_project(project_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    project = management.project_for(db, project_id, user, write=True)
    await management.publish(db, project)
    return management.detail(db, project, user)


@router.get("/{project_id}/rewards", response_model=list[RewardResponse])
def list_rewards(project_id: int, db: Session = Depends(get_db), user: User | None = Depends(get_optional_user)):
    project = management.project_for(db, project_id, user)
    stmt = select(RewardTier).where(RewardTier.project_id == project_id).order_by(RewardTier.price_cents, RewardTier.id)
    if not management.can_manage(db, project, user):
        stmt = stmt.where(RewardTier.active.is_(True))
    return db.scalars(stmt).all()


@router.post("/{project_id}/rewards", response_model=RewardResponse, status_code=201, dependencies=[Depends(require_trusted_origin)])
def create_reward(project_id: int, data: RewardCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    project = management.project_for(db, project_id, user, write=True)
    return management.save_reward(db, project, data)


@router.patch("/{project_id}/rewards/{tier_id}", response_model=RewardResponse, dependencies=[Depends(require_trusted_origin)])
def edit_reward(project_id: int, tier_id: int, data: RewardPatch, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    project = management.project_for(db, project_id, user, write=True)
    tier = db.get(RewardTier, tier_id)
    if tier is None or tier.project_id != project_id:
        raise HTTPException(404, 'Reward not found')
    return management.save_reward(db, project, data, tier)
