"""Public projections of authoritative records. No private evidence processing."""
from fastapi import HTTPException
from sqlalchemy import select, func, or_
from app.models.project import Project
from app.models.expense import Expense
from app.models.expense_document import ExpenseDocument
from app.services import accountability, documents


def public_project(db, project_id):
    project = db.get(Project, project_id)
    if project is None or project.status != 'active':
        raise HTTPException(404, 'Project not found')
    return project


def overview(db, project, public_context=None):
    # Always anonymous, even when the requester has a maintainer session.
    snapshot = accountability.snapshot(db, project, None, public_context=public_context)
    findings = [dict(category=item['category']) for item in snapshot['budget_variance'] if item['overspend_cents'] > 0]
    return dict(financial_summary=snapshot, public_findings=findings,
                public_unresolved_discrepancy_count=len(findings), last_updated_at=snapshot['calculated_at'])


def entry(expense, docs, findings):
    evidence = [dict(id=doc.id, detected_mime_type=doc.detected_mime_type) for doc in docs]
    return dict(id=expense.id, project_id=expense.project_id, currency=expense.currency, category=expense.category,
                vendor=expense.vendor, description=expense.description, amount_cents=expense.amount_cents,
                expense_date=expense.expense_date, updated_at=expense.updated_at, evidence=evidence,
                public_evidence_status='approved_redacted_document_attached' if evidence else 'self_reported',
                findings=[item for item in findings if item['category'] == expense.category.strip().casefold()])


def entries(db, project, rows, findings):
    ids = [row.id for row in rows]
    # Bound to this page; no private identifiers, filenames or keys leave this service.
    docs = db.scalars(select(ExpenseDocument).where(ExpenseDocument.expense_id.in_(ids),
        ExpenseDocument.publication_status == 'published', ExpenseDocument.redacted_from_id.is_not(None),
        ExpenseDocument.approved_by.is_not(None), ExpenseDocument.approved_at.is_not(None))
        .order_by(ExpenseDocument.created_at, ExpenseDocument.id)).all() if ids else []
    grouped = {}
    expenses = {row.id: row for row in rows}
    for doc in docs:
        if documents.is_public(doc, expenses[doc.expense_id], project):
            grouped.setdefault(doc.expense_id, []).append(doc)
    return [entry(row, grouped.get(row.id, []), findings) for row in rows]


def expense_query(project, q="", category="", evidence="all", date_from=None, date_to=None, category_values=None):
    stmt = select(Expense).where(Expense.project_id == project.id, Expense.publication_status == 'published')
    if q:
        value = q.lower()
        stmt = stmt.where(or_(*(func.lower(column).contains(value, autoescape=True) for column in [Expense.vendor, Expense.description, Expense.category])))
    if category_values is not None:
        stmt = stmt.where(Expense.category.in_(category_values))
    elif category:
        stmt = stmt.where(func.lower(func.trim(Expense.category)) == category.strip().lower())
    if evidence != 'all':
        approved = select(ExpenseDocument.id).where(ExpenseDocument.expense_id == Expense.id,
            ExpenseDocument.publication_status == 'published', ExpenseDocument.redacted_from_id.is_not(None),
            ExpenseDocument.approved_by.is_not(None), ExpenseDocument.approved_at.is_not(None)).exists()
        stmt = stmt.where(approved if evidence == 'supported' else ~approved)
    if date_from is not None:
        stmt = stmt.where(Expense.expense_date >= date_from)
    if date_to is not None:
        stmt = stmt.where(Expense.expense_date <= date_to)
    return stmt


def ledger(db, project, limit, offset, sort, q, category, evidence, date_from=None, date_to=None, summary=None, category_values=None):
    stmt = expense_query(project, q, category, evidence, date_from, date_to, category_values)
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    order = (Expense.expense_date.asc(), Expense.id.asc()) if sort == 'date_asc' else (Expense.expense_date.desc(), Expense.id.desc())
    rows = db.scalars(stmt.order_by(*order).limit(limit).offset(offset)).all()
    summary = summary if summary is not None else overview(db, project)
    return dict(project_id=project.id, items=entries(db, project, rows, summary['public_findings']), total=total,
                limit=limit, offset=offset, sort=sort, calculated_at=summary['last_updated_at'])


def detail(db, project, expense_id):
    expense = db.scalar(select(Expense).where(Expense.id == expense_id, Expense.project_id == project.id,
                                             Expense.publication_status == 'published'))
    if expense is None:
        raise HTTPException(404, 'Expense not found')
    return entries(db, project, [expense], overview(db, project)['public_findings'])[0]
