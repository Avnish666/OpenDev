
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.budget_allocation import BudgetAllocation
from app.schemas.project import ProjectCreate


def create_project(
    db: Session,
    owner_id: int,
    repo: dict,
    data: ProjectCreate,
) -> Project:

    # Validate budget categories.
    categories = [
        item.category.strip().casefold()
        for item in data.budget
    ]

    if len(categories) != len(set(categories)):
        raise HTTPException(
            status_code=422,
            detail="Duplicate budget categories",
        )

    # Validate total budget.
    total_budget = sum(
        item.allocated_cents for item in data.budget
    )

    if total_budget != data.funding_goal_cents:
        raise HTTPException(
            status_code=422,
            detail="Budget must equal funding goal",
        )

    project = Project(
        owner_id=owner_id,
        github_repo_id=repo["id"],
        github_repo_url=repo["url"],
        title=data.title,
        description=data.description,
        funding_goal_cents=data.funding_goal_cents,
        currency=data.currency,
        status="draft",
    )

    try:
        db.add(project)
        db.flush()

        # Add creator as the project owner.
        db.add(
            ProjectMember(
                project_id=project.id,
                user_id=owner_id,
                role="owner",
            )
        )

        # Save budget allocations.
        for allocation in data.budget:
            db.add(
                BudgetAllocation(
                    project_id=project.id,
                    category=allocation.category.strip(),
                    allocated_cents=allocation.allocated_cents,
                )
            )

        # All records commit together.
        db.commit()

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Project already exists or violates database constraints",
        )

    except Exception:
        db.rollback()
        raise

    db.refresh(project)
    return project
