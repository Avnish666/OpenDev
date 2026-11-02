from urllib.parse import urlparse
from fastapi import HTTPException
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.budget_allocation import BudgetAllocation
from app.models.reward_tier import RewardTier
from app.models.user import User
from app.services.github_repository import verify_repository_ownership


def can_manage(db, project, user):
    return bool(user and (project.owner_id == user.id or db.scalar(select(ProjectMember.id).where(
        ProjectMember.project_id == project.id, ProjectMember.user_id == user.id,
        ProjectMember.role == 'maintainer'))))


def project_for(db, project_id, user=None, write=False):
    project = db.scalar(select(Project).where(Project.id == project_id).with_for_update()) if write else db.get(Project, project_id)
    if project is None:
        raise HTTPException(404, 'Project not found')
    allowed = can_manage(db, project, user)
    if project.status != 'active' and not allowed:
        raise HTTPException(404, 'Project not found')
    if write and not allowed:
        raise HTTPException(403, 'Project owner or maintainer required')
    return project


def detail(db, project, user):
    members = select(ProjectMember.user_id).where(ProjectMember.project_id == project.id, ProjectMember.role.in_(['owner', 'maintainer']))
    return {**{k: getattr(project, k) for k in ['id','owner_id','github_repo_id','github_repo_url','title','description','funding_goal_cents','currency','status']},
            'budget': db.scalars(select(BudgetAllocation).where(BudgetAllocation.project_id == project.id)).all(),
            'maintainers': db.scalars(select(User).where((User.id == project.owner_id) | User.id.in_(members))).all(),
            'can_manage': can_manage(db, project, user)}


def commit(db):
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, 'Name already exists or database constraint violated')


def update_project(db, project, data):
    if project.status != 'draft':
        raise HTTPException(409, 'Only draft projects can be edited')
    values = data.model_dump(exclude_unset=True)
    budget = values.pop('budget', None)
    goal = values.get('funding_goal_cents', project.funding_goal_cents)
    current = budget if budget is not None else [dict(category=b.category, allocated_cents=b.allocated_cents) for b in db.scalars(select(BudgetAllocation).where(BudgetAllocation.project_id == project.id))]
    names = [b['category'].strip().casefold() for b in current]
    if any(not n for n in names) or len(set(names)) != len(names) or sum(b['allocated_cents'] for b in current) != goal:
        raise HTTPException(422, 'Budget categories must be unique and budget must equal funding goal')
    for k, v in values.items():
        setattr(project, k, v)
    if budget is not None:
        for b in db.scalars(select(BudgetAllocation).where(BudgetAllocation.project_id == project.id)):
            db.delete(b)
        db.flush()
        for b in budget:
            db.add(BudgetAllocation(project_id=project.id, category=b['category'].strip(), allocated_cents=b['allocated_cents']))
    commit(db)
    return project


async def publish(db, project):
    if project.status != 'draft':
        raise HTTPException(409, 'Only drafts can be published')
    total = db.scalar(select(func.sum(BudgetAllocation.allocated_cents)).where(BudgetAllocation.project_id == project.id))
    if total != project.funding_goal_cents:
        raise HTTPException(422, 'Budget must equal funding goal')
    owner = db.get(User, project.owner_id)
    url = urlparse(project.github_repo_url)
    if not owner or owner.github_id is None or url.scheme != 'https' or url.netloc != 'github.com':
        raise HTTPException(422, 'Invalid repository association')
    repo = await verify_repository_ownership(url.path.strip('/'), owner.github_id)
    if repo['id'] != project.github_repo_id:
        raise HTTPException(422, 'Repository association changed')
    project.status = 'active'
    commit(db)
    return project


def save_reward(db, project, data, tier=None):
    values = data.model_dump(exclude_unset=tier is not None)
    if values.get('currency', project.currency) != project.currency:
        raise HTTPException(422, 'Reward currency must match project currency')
    if tier is None:
        tier = RewardTier(project_id=project.id, **values)
        db.add(tier)
    else:
        for k, v in values.items():
            setattr(tier, k, v)
    commit(db)
    db.refresh(tier)
    return tier
