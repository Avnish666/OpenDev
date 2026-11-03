"""Read-only adapters over authoritative financial/progress/public history services."""
from app.schemas.dashboard_filters import DashboardDimensions
from fastapi import HTTPException
from sqlalchemy import select, func
from app.models.project import Project
from app.models.expense import Expense
from app.models.expense_document import ExpenseDocument
from app.models.funding import Contribution
from app.models.roadmap import ProjectRoadmapMilestone as Milestone, MilestoneStatusHistory as History
from app.services import transparency, credibility, accountability, analytics_development
from app.schemas.analytics import AnalyticsOverview, ExpenseFilters


def expense_analysis(db, project, filters, category_values=None):
    # Same public/evidence predicates as the ledger. EXISTS avoids document fan-out.
    source = transparency.expense_query(project, category=filters.category, evidence=filters.evidence,
        date_from=filters.date_from, date_to=filters.date_to, category_values=category_values).subquery()
    groups = []
    for key, cap in [(source.c.category, 10000),
                     (func.to_char(source.c.expense_date, 'YYYY-MM'), 120)]:
        rows = db.execute(select(key.label('key'), func.count().label('expense_count'),
            func.sum(source.c.amount_cents).label('amount_cents')).group_by(key).order_by(key).limit(cap + 1)).mappings().all()
        if len(rows) > cap:
            raise HTTPException(413, 'Expense groups exceed analytics capacity; narrow the filters')
        groups.append([dict(row) for row in rows])
    # Match authoritative budgeting's Unicode strip/casefold normalization.
    categories = {}
    for row in groups[0]:
        key = row['key'].strip().casefold()
        bucket = categories.setdefault(key, dict(key=key, expense_count=0, amount_cents=0))
        bucket['expense_count'] += row['expense_count']
        bucket['amount_cents'] += row['amount_cents']
    if len(categories) > 200:
        raise HTTPException(413, 'Expense groups exceed analytics capacity; narrow the filters')
    groups[0] = [categories[key] for key in sorted(categories)]
    count, amount = db.execute(select(func.count(), func.coalesce(func.sum(source.c.amount_cents), 0))).one()
    return dict(categories=groups[0], months=groups[1], expense_count=count, reported_spending_cents=amount)


def overview(db,project_id,limit=50,offset=0,filters=None,milestone_offset=0,dimensions=None,*,expense_limit=None,milestone_limit=None):
    dimensions=dimensions or DashboardDimensions()
    filters = filters or ExpenseFilters()
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
    projects=db.scalars(select(Project).where(Project.id.in_(owned)).order_by(Project.id)).all()
    context=accountability.public_sources(db,projects)
    summary=transparency.overview(db,p,public_context=context)
    s=summary['financial_summary']
    category_values = None
    if filters.category or dimensions.discrepancy!='all':
        # Bounded by source preflight. Resolve exact canonical categories once, not per row.
        category_values = [value for value in db.scalars(select(Expense.category).where(
            Expense.project_id == p.id, Expense.publication_status == 'published').distinct())
            if (not filters.category or value.strip().casefold()==filters.category.strip().casefold()) and
            (dimensions.discrepancy=='all' or ((value.strip().casefold() in {r['category'] for r in s['budget_variance'] if r['overspend_cents']>0}) == (dimensions.discrepancy=='with')))]
    ledger=transparency.ledger(db,p,expense_limit or limit,offset,filters.sort,'',filters.category,filters.evidence,filters.date_from,filters.date_to,summary=summary,category_values=category_values)
    grouped_expenses=expense_analysis(db,p,filters,category_values)
    rows=db.scalars(select(Milestone).where(Milestone.project_id.in_(owned)).order_by(Milestone.id)).all()
    derived=credibility.delivery_rows(db,rows)
    development=analytics_development.dataset(db,p,s['calculated_at'],derived,milestone_limit or limit,milestone_offset,dimensions)
    profile=credibility.profile(db,p.owner_id,s['calculated_at'],public_context=context,
        milestone_rows=rows,delivery_history=derived,include_github=False)
    result=AnalyticsOverview.model_validate(dict(project_id=p.id,currency=p.currency,as_of=s['calculated_at'],funding_goal_cents=p.funding_goal_cents,
        financial=s,budget=s['budget_variance'],expenses=[dict(id=r['id'],category=r['category'],amount_cents=r['amount_cents'],currency=r['currency'],expense_date=r['expense_date'],
            approved_public_support=bool(r['evidence']),public_category_finding_count=len(r['findings'])) for r in ledger['items']],
        expense_analysis=grouped_expenses,expense_filters=filters,public_unresolved_finding_count=summary['public_unresolved_discrepancy_count'],funding_trend={},
        expense_total=ledger['total'],expense_limit=ledger['limit'],expense_offset=offset,
        dashboard_filters=dimensions,development=development,
        maintainer=dict(project_rewards=credibility.reward_statistics(db,[p],s['calculated_at']),owner_id=p.owner_id,participation=profile['participation'],delivery=profile['delivery'],rewards=profile['rewards'],financial=profile['financial'],scope=profile['scope'],attribution=profile['attribution']),
        limitations=[*s['notes'],*profile['limitations'],*analytics_development.LIMITATIONS,
            'Expense and milestone rows are bounded pages. Financial/category totals and development counts use their full current public source scope.',
            'Expense filters apply to the expense grid and category/month breakdowns only. Funding, budget and evidence overview remain full-project totals.',
            'Months use maintainer-reported expense dates, not receipt uploads or PayPal capture dates. Missing months are not observations and are not filled with zeros.',
            'Without public supporting documents does not mean private documents do not exist. Documents do not prove vendor payment.',
            'This endpoint is public-only even for owners. No private receipt IDs, OCR, reviewer notes, backer identities or storage metadata are included.']))
    if len(result.model_dump_json().encode())>262144:raise HTTPException(413,'Analytics response exceeds capacity')
    return result
