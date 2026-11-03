"""Read-only adapters over authoritative financial/progress/public history services."""
from fastapi import HTTPException
from sqlalchemy import select, func
from app.models.project import Project
from app.models.expense import Expense
from app.models.expense_document import ExpenseDocument
from app.models.funding import Contribution
from app.models.roadmap import ProjectRoadmapMilestone as Milestone, MilestoneStatusHistory as History
from app.services import transparency, progress, credibility
from app.schemas.analytics import AnalyticsOverview


def overview(db,project_id,limit=50,offset=0):
    p=transparency.public_project(db,project_id)
    owned=credibility.owned_ids(p.owner_id)
    if db.scalar(select(func.count()).select_from(Project).where(Project.id.in_(owned)))>20:
        raise HTTPException(413,'Public owner scope exceeds analytics capacity')
    for model,condition in [(Expense,Expense.project_id.in_(owned)),(Contribution,Contribution.project_id.in_(owned)),
                            (ExpenseDocument,ExpenseDocument.expense_id.in_(select(Expense.id).where(Expense.project_id.in_(owned)))),
                            (Milestone,Milestone.project_id.in_(owned)),
                            (History,History.milestone_id.in_(select(Milestone.id).where(Milestone.project_id.in_(owned))))]:
        if db.scalar(select(func.count()).select_from(model).where(condition))>10000:
            raise HTTPException(413,'Public source scope exceeds analytics capacity')
    summary=transparency.overview(db,p)
    s=summary['financial_summary']
    ledger=transparency.ledger(db,p,limit,offset,'date_desc','','','all')
    development=progress.summary(db,p.id)
    profile=credibility.profile(db,p.owner_id,s['calculated_at'])
    # The project page is scoped independently from owner-wide history pagination.
    rows=db.scalars(select(Milestone).where(Milestone.project_id==p.id).order_by(Milestone.id).limit(limit).offset(offset)).all()
    milestones=credibility.delivery_rows(db,rows)
    result=AnalyticsOverview.model_validate(dict(project_id=p.id,currency=p.currency,as_of=s['calculated_at'],funding_goal_cents=p.funding_goal_cents,
        financial=s,budget=s['budget_variance'],expenses=[dict(id=r['id'],category=r['category'],amount_cents=r['amount_cents'],currency=r['currency'],expense_date=r['expense_date'],
            approved_public_support=bool(r['evidence']),public_category_finding_count=len(r['findings'])) for r in ledger['items']],
        expense_total=ledger['total'],expense_limit=limit,expense_offset=offset,
        development=dict(counts=development['counts'],milestones=milestones,total=development['counts']['total'],limit=limit,offset=offset,
            github_counts=development['activity']['counts'] if development['activity'] else None,last_successful_sync_at=development['sync']['last_successful_sync_at'],github_stale=development['sync']['stale']),
        maintainer=dict(owner_id=p.owner_id,participation=profile['participation'],delivery=profile['delivery'],rewards=profile['rewards'],financial=profile['financial'],scope=profile['scope'],attribution=profile['attribution']),
        limitations=[*s['notes'],*profile['limitations'],
            'Expense and milestone rows are bounded pages. Financial/category totals and development counts use their full current public source scope.',
            'No historical funding trend or comparable activity time windows are available. Calculation time is not settlement or source-update time.',
            'This endpoint is public-only even for owners. No private receipt IDs, OCR, reviewer notes, backer identities or storage metadata are included.']))
    if len(result.model_dump_json().encode())>262144:raise HTTPException(413,'Analytics response exceeds capacity')
    return result
