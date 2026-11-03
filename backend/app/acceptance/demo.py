"""Synthetic local demo fixture. No auth override, provider calls or destructive reset."""
import argparse
import hashlib
import json
import os
import re
from datetime import date, datetime, timezone
from uuid import NAMESPACE_URL, uuid5

STAMP = datetime(2026, 10, 1, 12, tzinfo=timezone.utc)
PREFIX = '[LOCAL DEMO] '
REPO_ID = 970000001
QUESTIONS = [
    ('funding', 'How much funding has the project received?'),
    ('spending', 'What is the reported spending by category?'),
    ('findings', 'What discrepancies have been publicly disclosed?'),
    ('overdue', 'Which milestones are overdue?'),
    ('deadlines', 'Which commitments were delayed or rescheduled?'),
    ('github', 'What GitHub activity is available?'),
    ('cross_domain', 'Are the reported expenses increasing while delivery is delayed?'),
    ('limitations', 'What financial information is missing?'),
]


def identifier(name):
    return str(uuid5(NAMESPACE_URL, 'opendev-local-demo-v1/' + name))


def local_database():
    # Do not import app config (which can load dotenv) before validating the target.
    from sqlalchemy.engine import make_url
    if os.getenv('APP_ENV') != 'testing' or os.getenv('OPENDEV_DEMO') != 'synthetic-local':
        raise ValueError('Explicit local synthetic demo environment required')
    if any(os.getenv(k) != 'false' for k in ('CHECKOUT_ENABLED', 'RECEIPT_PROCESSING_ENABLED', 'LLM_ENABLED')):
        raise ValueError('Demo must disable checkout, receipt processing and LLM')
    url = make_url(os.getenv('DATABASE_URL', ''))
    if url.drivername not in ('postgresql', 'postgresql+psycopg') or url.host not in ('127.0.0.1', 'localhost', '::1') or not re.fullmatch(r'opendev_test_demo_[a-z0-9_]+', url.database or ''):
        raise ValueError('Dedicated loopback opendev_test_demo_* database required')
    if any(k != 'options' for k in url.query) or (url.query.get('options') and not re.fullmatch(r'-csearch_path=[a-z_0-9]+', url.query['options'])):
        raise ValueError('Database connection overrides rejected')
    return url


def demo_engine():
    from sqlalchemy import create_engine
    url = local_database()
    return create_engine(url, connect_args={'hostaddr': '::1' if url.host == '::1' else '127.0.0.1', 'connect_timeout': 3}, pool_size=3, max_overflow=0)


def seed(engine):
    from sqlalchemy import select, text, func
    from sqlalchemy.orm import Session
    from app.models.user import User
    from app.models.project import Project
    from app.models.project_member import ProjectMember
    from app.models.budget_allocation import BudgetAllocation
    from app.models.reward_tier import RewardTier
    from app.models.funding import Contribution, Entitlement, WebhookEvent, RefundRecord
    from app.models.expense import Expense
    from app.models.expense_document import ExpenseDocument
    from app.models.roadmap import ProjectRoadmapMilestone as Milestone, MilestoneStatusHistory as History, MilestoneGitHubEvidence as Link
    from app.models.roadmap_dependency import RoadmapDependency
    from app.models.github_progress import GitHubRepositorySnapshot as Repository, GitHubSyncRun as Sync, GitHubIssueSnapshot as Issue, GitHubPullRequestSnapshot as Pull
    with Session(engine) as db, db.begin():
        db.execute(text('SELECT pg_advisory_xact_lock(970000001)'))
        existing = db.scalar(select(Project).where(Project.github_repo_id == REPO_ID))
        if existing:
            if existing.title != PREFIX + 'OpenDev Observatory' or db.get(User, existing.owner_id).username != 'opendev-demo-maintainer':
                raise ValueError('Fixture ownership mismatch; no data changed')
            main = existing
        else:
            if db.scalar(select(func.count()).select_from(User)) or db.scalar(select(func.count()).select_from(Project)):
                raise ValueError('Seed requires an empty migrated demo database; no reset performed')
            owner = User(username='opendev-demo-maintainer', github_id=970000001, created_at=STAMP)
            backer = User(username='opendev-demo-backer', github_id=970000002, created_at=STAMP)
            db.add_all([owner, backer]); db.flush()
            def campaign(number, title, status='active'):
                row = Project(owner_id=owner.id, github_repo_id=REPO_ID+number,
                    github_repo_url=f'https://github.com/opendev-demo-fixtures/campaign-{number}',
                    title=PREFIX+title, description='Synthetic local demonstration data. Repository references, funding, refunds, receipts and GitHub observations are fixtures, not live-provider verification. No real funds or personal documents.',
                    funding_goal_cents=100000, currency='USD', status=status, created_at=STAMP, updated_at=STAMP)
                db.add(row); db.flush()
                db.add(ProjectMember(project_id=row.id, user_id=owner.id, role='owner', joined_at=STAMP))
                for category, amount in [('Development', 60000), ('Hosting', 20000), ('Documentation', 20000)]:
                    db.add(BudgetAllocation(project_id=row.id, category=category, allocated_cents=amount, created_at=STAMP))
                return row
            main = campaign(0, 'OpenDev Observatory')
            history = campaign(1, 'Earlier release records')
            campaign(2, 'Private planning fixture', 'draft')
            tier = RewardTier(project_id=main.id, name=PREFIX+'Early supporter', description='Synthetic reward; not a purchase. Unlimited tier avoids abandoned limited reservations.', price_cents=5000, currency='USD', benefits=[{'title':'Demo release notes','description':'Maintainer-asserted fulfillment fixture'}], quantity_limit=None, active=True, created_at=STAMP, updated_at=STAMP)
            db.add(tier); db.flush()
            for n, (status, amount, refund, entitlement) in enumerate([
                ('completed', 50000, None, 'fulfilled'), ('completed', 30000, None, 'granted'),
                ('refunded', 20000, 5000, 'revoked'), ('reversed', 10000, None, 'revoked')]):
                c = Contribution(id=identifier(f'contribution-{n}'), user_id=backer.id, project_id=main.id, tier_id=tier.id,
                    checkout_key=identifier(f'checkout-{n}'), amount_cents=amount, refund_total_cents=refund, currency='USD',
                    reward_snapshot={'name':tier.name,'description':tier.description,'benefits':tier.benefits}, status=status,
                    order_id=f'DEMO-ORDER-{n}', capture_id=f'DEMO-CAPTURE-{n}', capture_key=identifier(f'capture-{n}'), created_at=STAMP)
                db.add(c); db.flush()
                db.add(Entitlement(id=identifier(f'entitlement-{n}'), contribution_id=c.id, status=entitlement, fulfillment_note='DEMO_PRIVATE_BACKER_NOTE', created_at=STAMP))
                event = WebhookEvent(id=f'DEMO-EVENT-{n}', event_type='PAYMENT.CAPTURE.REFUNDED' if status=='refunded' else 'PAYMENT.CAPTURE.REVERSED' if status=='reversed' else 'PAYMENT.CAPTURE.COMPLETED', created_at=STAMP)
                db.add(event); db.flush()
                if refund:
                    db.add(RefundRecord(id='DEMO-REFUND-1', contribution_id=c.id, capture_id=c.capture_id, event_id=event.id, amount_cents=refund, provider_total_cents=refund, currency='USD', observed_at=STAMP))
            expenses=[]
            for n, (category, amount, published) in enumerate([('Development',35000,True),('Hosting',25000,True),('Documentation',5000,True),('Hosting',999,False)]):
                expense = Expense(project_id=main.id, submitted_by_user_id=owner.id, category=category, amount_cents=amount, currency='USD', vendor='Synthetic Demo Vendor' if published else 'DEMO_PRIVATE_VENDOR', description='Synthetic published spending report; not verified vendor payment.' if published else 'DEMO_PRIVATE_EXPENSE', expense_date=date(2026,10,n+1), publication_status='published' if published else 'draft', created_at=STAMP, updated_at=STAMP)
                db.add(expense); db.flush(); expenses.append(expense)
            original = ExpenseDocument(id=identifier('original'), expense_id=expenses[1].id, uploaded_by=owner.id, storage_key='DEMO_PRIVATE_STORAGE_KEY', original_filename='DEMO_PRIVATE_FILENAME.pdf', detected_mime_type='application/pdf', file_size_bytes=100, sha256_hash=hashlib.sha256(b'synthetic metadata only, no stored original').hexdigest(), publication_status='private', created_at=STAMP)
            db.add(original); db.flush()
            db.add(ExpenseDocument(id=identifier('redacted'), expense_id=expenses[1].id, uploaded_by=owner.id, storage_key='DEMO_PUBLIC_METADATA_ONLY', original_filename='synthetic-redaction-metadata.pdf', detected_mime_type='application/pdf', file_size_bytes=100, sha256_hash=hashlib.sha256(b'synthetic metadata only, no stored redaction').hexdigest(), publication_status='published', redacted_from_id=original.id, approved_by=owner.id, approved_at=STAMP, created_at=STAMP))
            db.add_all([
                Repository(project_id=main.id, github_repo_id=main.github_repo_id, publicly_accessible=True, metadata_json={'id':main.github_repo_id,'full_name':'opendev-demo-fixtures/campaign-0','private':False,'default_branch':'main','updated_at':STAMP.isoformat(),'pushed_at':STAMP.isoformat(),'description':'Synthetic fixture, not a live repository'}, recent_commits=[{'sha':'a'*40,'message':'Synthetic fixture: publish evidence schema','committed_at':STAMP.isoformat(),'html_url':'https://github.com/opendev-demo-fixtures/campaign-0/commit/'+'a'*40}], last_synced_at=STAMP),
                Sync(id=identifier('sync'), project_id=main.id, status='completed', started_at=STAMP, completed_at=STAMP, counters={'issues':1,'pull_requests':1}),
                Issue(project_id=main.id, github_id=970000101, number=1, title=PREFIX+'Evidence schema', state='closed', created_at=STAMP, updated_at=STAMP, closed_at=STAMP, last_synced_at=STAMP),
                Pull(project_id=main.id, github_id=970000201, number=2, title=PREFIX+'Add roadmap evidence', state='closed', created_at=STAMP, updated_at=STAMP, merged_at=STAMP, last_synced_at=STAMP),
            ]); db.flush()
            def milestone(project, name, status, original_end, revised=None, actual=None, order=0):
                m=Milestone(project_id=project.id,title=PREFIX+name, description='Synthetic roadmap commitment', deliverable_description='Fixture deliverable; delivery is a maintainer assertion', planned_start_date=date(2026,9,1), planned_end_date=date.fromisoformat(revised or original_end), actual_completion_date=date.fromisoformat(actual) if actual else None, status=status, version=1, display_order=order, created_by=owner.id, created_at=STAMP, updated_at=STAMP)
                db.add(m);db.flush()
                transitions=[('created','planned',{'planned_end_date':original_end,'status':'planned'})]
                if revised:transitions.append(('edited','planned',{'planned_end_date':revised,'status':'planned'}))
                if status in ('in_progress','delivered'):transitions.append(('status_changed','in_progress',{'status':'in_progress'}))
                if status=='delivered':transitions.extend([('status_changed','submitted_for_review',{'status':'submitted_for_review'}),('status_changed','delivered',{'status':'delivered','actual_completion_date':actual})])
                previous=None
                for version,(action,new,after) in enumerate(transitions,1):
                    db.add(History(id=identifier(f'history-{m.id}-{version}'), milestone_id=m.id, version=version, previous_status=previous, new_status=new, actor_id=owner.id, action=action, reason='Synthetic demo history', before_json={'status':previous}, after_json=after, created_at=STAMP));previous=new
                m.version=len(transitions)
                return m
            delivered=milestone(main,'Public evidence schema','delivered','2026-10-05',actual='2026-10-04')
            overdue=milestone(main,'Documentation and release','in_progress','2026-10-10',revised='2026-10-20',order=1)
            milestone(main,'Community feedback','planned','2027-12-01',order=2)
            milestone(history,'Earlier documented release','delivered','2026-09-20',actual='2026-09-22')
            db.add(RoadmapDependency(project_id=main.id,from_id=delivered.id,to_id=overdue.id))
            db.add(Link(id=identifier('issue-link'),milestone_id=delivered.id,project_id=main.id,evidence_type='issue',canonical_id='970000101',issue_snapshot_id=970000101,linked_snapshot_json={'title':PREFIX+'Evidence schema','state':'closed','number':1,'merged':None,'observed_at':STAMP.isoformat(),'repo_name':'opendev-demo-fixtures/campaign-0'},created_by=owner.id,created_at=STAMP))
            db.add(Link(id=identifier('pr-link'),milestone_id=delivered.id,project_id=main.id,evidence_type='pull_request',canonical_id='970000201',pr_snapshot_id=970000201,linked_snapshot_json={'title':PREFIX+'Add roadmap evidence','state':'closed','number':2,'merged':True,'observed_at':STAMP.isoformat(),'repo_name':'opendev-demo-fixtures/campaign-0'},created_by=owner.id,created_at=STAMP))
            db.flush()
        projects=db.scalars(select(Project).order_by(Project.id)).all()
        expense=db.scalar(select(Expense).where(Expense.project_id==main.id,Expense.publication_status=='published',Expense.category=='Hosting'))
        return {'scope':'LOCAL SYNTHETIC DEMO; no live-provider verification', 'fixture_version':1, 'project_id':main.id, 'owner_id':main.owner_id, 'expense_id':expense.id,
            'public_project_ids':[p.id for p in projects if p.status=='active'], 'private_project_id':next(p.id for p in projects if p.status=='draft'),
            'expected':{'gross_captured_cents':110000,'refund_exclusion_cents':5000,'reversal_exclusion_cents':10000,'net_recorded_cents':95000,'published_spending_cents':65000,'difference_cents':30000,'public_findings':1,'public_documents':1},
            'notes':['All monetary/provider/GitHub records are synthetic.', 'Receipt metadata only; no objects exist in Supabase. Do not click download as live storage evidence.', 'Exact refund total remains null due to unknown reversal refund coverage.', 'Owner aggregates cover currently active public projects, not a previous-project cohort.'],
            'questions':[{'key':k,'question':q} for k,q in QUESTIONS]}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--environment',choices=['local-test'],required=True)
    args=parser.parse_args()
    engine=None
    try:
        engine=demo_engine()
        print(json.dumps(seed(engine),indent=2))
        return 0
    except Exception:
        print(json.dumps({'status':'blocked','reason':'Invalid demo setup or fixture conflict; details withheld. Use a dedicated empty migrated local demo database.'}))
        return 2
    finally:
        if engine is not None:engine.dispose()


if __name__=='__main__':raise SystemExit(main())
