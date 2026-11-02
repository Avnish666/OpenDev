"""Expense writes and deterministic financial reporting, without PayPal side effects."""
from fastapi import HTTPException
from sqlalchemy import literal, select, func, union_all
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.expense import Expense
from app.models.project import Project
from app.models.user import User
from app.models.budget_allocation import BudgetAllocation
from app.models.funding import Contribution
from app.schemas.expense import ExpenseCreate, ExpensePatch
from app.services.project_management import can_manage


def project_for_expenses(db: Session, project_id: int, user: User | None = None, *, write: bool = False) -> Project:
    # All expense writes lock the project before the expense to keep lock ordering consistent.
    stmt = select(Project).where(Project.id == project_id)
    if write:
        stmt = stmt.with_for_update().execution_options(populate_existing=True)
    project = db.scalar(stmt)
    if project is None or (project.status == 'draft' and not can_manage(db, project, user)):
        raise HTTPException(404, 'Project not found')
    if write and not can_manage(db, project, user):
        raise HTTPException(403, 'Project owner or maintainer required')
    return project


def commit(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, 'Expense violates database constraints') from None
    except Exception:
        db.rollback()
        raise


def create(db: Session, project_id: int, user: User, data: ExpenseCreate) -> Expense:
    project = project_for_expenses(db, project_id, user, write=True)
    if project.status == 'draft':
        raise HTTPException(409, 'Publish the project before recording expenses')
    if data.currency != project.currency:
        raise HTTPException(422, 'Expense currency must match project currency')
    expense = Expense(project_id=project.id, submitted_by_user_id=user.id, **data.model_dump())
    db.add(expense)
    commit(db)
    db.refresh(expense)
    return expense


def get(db: Session, expense_id: int, user: User | None = None, *, write: bool = False) -> Expense:
    # project_id is immutable through the API; inspect it before locking parent then child.
    expense = db.get(Expense, expense_id)
    if expense is None:
        raise HTTPException(404, 'Expense not found')
    project = project_for_expenses(db, expense.project_id, user, write=write)
    if write:
        expense = db.scalar(select(Expense).where(Expense.id == expense_id).with_for_update().execution_options(populate_existing=True))
    if expense.publication_status != 'published' and not can_manage(db, project, user):
        raise HTTPException(404, 'Expense not found')
    return expense


def edit(db: Session, expense_id: int, user: User, data: ExpensePatch) -> Expense:
    expense = get(db, expense_id, user, write=True)
    if expense.publication_status != 'draft':
        raise HTTPException(409, 'Published expenses are immutable')
    if data.currency is not None and data.currency != db.get(Project, expense.project_id).currency:
        raise HTTPException(422, 'Expense currency must match project currency')
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(expense, key, value)
    commit(db)
    db.refresh(expense)
    return expense


def publish(db: Session, expense_id: int, user: User) -> Expense:
    expense = get(db, expense_id, user, write=True)
    expense.publication_status = 'published'
    commit(db)
    db.refresh(expense)
    return expense


def summary(db: Session, project: Project) -> dict:
    # One SQL statement gives one PostgreSQL snapshot for budgets, spending and funding.
    # Do not join these one-to-many tables: that would multiply the monetary totals.
    budgets = select(literal('budget').label('kind'), BudgetAllocation.category.label('category'), literal(project.currency).label('currency'), BudgetAllocation.allocated_cents.label('amount'), literal(0).label('count')).where(BudgetAllocation.project_id == project.id)
    spending = select(literal('spending'), Expense.category, Expense.currency, func.sum(Expense.amount_cents), func.count()).where(Expense.project_id == project.id, Expense.publication_status == 'published').group_by(Expense.category, Expense.currency)
    funding = select(literal('funding'), Contribution.status, Contribution.currency, func.sum(Contribution.amount_cents), func.count()).where(Contribution.project_id == project.id, Contribution.capture_id.is_not(None)).group_by(Contribution.status, Contribution.currency)
    categories: dict[str, dict] = {}
    completed = excluded_refunded = excluded_other = mismatches = expense_count = 0
    for row in db.execute(union_all(budgets, spending, funding)):
        amount = int(row.amount)
        if row.currency != project.currency:
            mismatches += int(row._mapping['count'])
            continue
        if row.kind == 'funding':
            if row.category == 'completed':
                completed += amount
            elif row.category in ('refunded', 'reversed'):
                excluded_refunded += amount
            else:
                excluded_other += amount
            continue
        key = row.category.strip().casefold()
        category = categories.setdefault(key, dict(category=key, allocated_cents=0, reported_spending_cents=0, independently_verified_spending_cents=0))
        category['allocated_cents' if row.kind == 'budget' else 'reported_spending_cents'] += amount
        if row.kind == 'spending':
            expense_count += int(row._mapping['count'])
    for category in categories.values():
        category['budget_remaining_cents'] = category['allocated_cents'] - category['reported_spending_cents']
        category['overspend_cents'] = max(0, -category['budget_remaining_cents'])
    allocated = sum(c['allocated_cents'] for c in categories.values())
    reported = sum(c['reported_spending_cents'] for c in categories.values())
    return dict(project_id=project.id, currency=project.currency, completed_funding_cents=completed, excluded_refunded_or_reversed_cents=excluded_refunded, excluded_other_status_cents=excluded_other, excluded_currency_mismatch_count=mismatches, reported_spending_cents=reported, independently_verified_spending_cents=0, allocated_budget_cents=allocated, budget_remaining_cents=allocated-reported, funding_less_reported_spending_cents=completed-reported, expense_count=expense_count, categories=[categories[k] for k in sorted(categories)])
