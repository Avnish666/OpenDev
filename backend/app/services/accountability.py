"""Deterministic, read-only reconciliation with a separate human-opinion overlay."""
from contextlib import contextmanager
import hashlib
import json
from uuid import UUID, uuid4

from fastapi import HTTPException
from sqlalchemy import select, text, func
from sqlalchemy.orm import Session
from app.models.project import Project
from app.models.budget_allocation import BudgetAllocation
from app.models.expense import Expense
from app.models.expense_document import ExpenseDocument
from app.models.funding import Contribution
from app.models.receipt_extraction import ReceiptExtraction
from app.models.finding_review import FindingReview
from app.schemas.extraction import ExtractedReceipt
from app.services import expenses, documents
from app.services.project_management import can_manage
from app.services.receipt import pipeline
from app.services.receipt.findings import detect, normalize


@contextmanager
def read_snapshot(db):
    # Auth sessions may already have an active READ COMMITTED transaction. A distinct
    # read-only transaction gives all contributing SELECTs a single MVCC snapshot.
    with db.get_bind().engine.connect().execution_options(isolation_level='REPEATABLE READ') as conn:
        with conn.begin():
            conn.execute(text('SET TRANSACTION READ ONLY'))
            with Session(bind=conn,autoflush=False) as reader:
                yield reader


def reference(record, finding):
    body={key:value for key,value in finding.items() if key not in ('review_status','id','resolved')}
    digest=hashlib.sha256(json.dumps(body,sort_keys=True,separators=(',',':'),default=str).encode()).hexdigest()[:32]
    return record.id+':'+digest


def selected_records(db,docs):
    if not docs:return {}
    records=db.scalars(select(ReceiptExtraction).where(ReceiptExtraction.expense_document_id.in_([d.id for d in docs])).order_by(ReceiptExtraction.created_at.desc(),ReceiptExtraction.id.desc())).all()
    selected={}
    for record in records:
        previous=selected.get(record.expense_document_id)
        if previous is None or (record.extraction_version==pipeline.VERSION and previous.extraction_version!=pipeline.VERSION):
            selected[record.expense_document_id]=record
    return selected


def raw_findings(db,record,expense,doc):
    if record.extraction_status=='completed' and record.extracted_json:
        return detect(db,doc,expense,ExtractedReceipt.model_validate(record.extracted_json))
    if record.extraction_status=='failed':
        return [dict(finding_code='EXTRACTION_FAILED',severity='info',reported_value=None,extracted_value=None,
                     explanation='Extraction failed; a human may request a bounded retry.',evidence_reference={'processing_error_code':record.processing_error_code})]
    return []


def finding_views(db,record,expense,doc):
    output=[]
    reviews=db.scalars(select(FindingReview).where(FindingReview.extraction_id==record.id).order_by(FindingReview.created_at,FindingReview.id)).all()
    for finding in raw_findings(db,record,expense,doc):
        fid=reference(record,finding)
        relevant=[r for r in reviews if r.finding_reference==fid]
        status='human_review_required'
        for review in relevant:
            status={'mark_reviewed':'reviewed','accept_field':'accepted','dispute_field':'disputed'}.get(review.action,status)
        output.append({**finding,'id':fid,'extraction_id':record.id,'review_status':status,'resolved':False})
    return output


def verification(db,expense,user):
    project=db.get(Project,expense.project_id)
    private=can_manage(db,project,user)
    stmt=select(ExpenseDocument).where(ExpenseDocument.expense_id==expense.id)
    docs=db.scalars(stmt).all()
    public_docs=[d for d in docs if documents.is_public(d,expense,project)]
    visible=docs if private else public_docs
    states=['self_reported'];findings=[];records={}
    if visible:states.append('document_attached')
    if private:
        originals=[d for d in docs if not d.redacted_from_id]
        records=selected_records(db,originals)
        for doc in docs:
            if doc.id in records:findings.extend(finding_views(db,records[doc.id],expense,doc))
        if findings:states.append('discrepancy_detected')
        complete=bool(records) and len(records)==len(originals) and all(r.extraction_status=='completed' and r.extracted_json for r in records.values())
        consistent=complete and not findings
        if consistent:
            for record in records.values():
                receipt=ExtractedReceipt.model_validate(record.extracted_json)
                if any(getattr(receipt,name).value is None or getattr(receipt,name).confidence!='high' for name in ['vendor_name','document_date','currency','total_cents']):consistent=False
        if consistent:states.append('extraction_consistent')
        if records and db.scalar(select(func.count()).select_from(FindingReview).where(FindingReview.extraction_id.in_([r.id for r in records.values()]))):states.append('human_reviewed')
    classification=next((state for state in ['discrepancy_detected','human_reviewed','extraction_consistent','document_attached'] if state in states),'self_reported')
    return dict(expense_id=expense.id,publication_status=expense.publication_status,amount_cents=expense.amount_cents,currency=expense.currency,
                audience='manager_private' if private else 'public_evidence_only',evidence_states=states,classification=classification,
                approved_public_document_ids=[d.id for d in public_docs],supporting_document_count=len(visible),
                unresolved_discrepancy_count=len({f['finding_code'] for f in findings}) if private else None,
                findings=findings,reviews_available=private)


def snapshot(db,project,user):
    private=can_manage(db,project,user)
    gross=refunds=reversals=0
    # Contributions are never joined to receipts, reviews, attempts or webhook rows.
    seen=set()
    for contribution in db.scalars(select(Contribution).where(Contribution.project_id==project.id,Contribution.currency==project.currency,Contribution.capture_id.is_not(None))):
        if contribution.capture_id in seen:continue
        seen.add(contribution.capture_id)
        if contribution.status in ('completed','refunded','reversed'):
            gross+=contribution.amount_cents
            if contribution.status=='refunded':refunds+=contribution.amount_cents
            if contribution.status=='reversed':reversals+=contribution.amount_cents
    net=gross-refunds-reversals
    published=db.scalars(select(Expense).where(Expense.project_id==project.id,Expense.publication_status=='published',Expense.currency==project.currency)).all()
    coverage={};with_count=with_amount=unresolved_expenses=unresolved_count=0
    categories={}
    for allocation in db.scalars(select(BudgetAllocation).where(BudgetAllocation.project_id==project.id)):
        key=allocation.category.strip().casefold()
        categories.setdefault(key,dict(category=key,allocated_cents=0,reported_spending_cents=0))['allocated_cents']+=allocation.allocated_cents
    public_support=set()
    if not private and project.status in ('active','paused','completed'):
        public_support=set(db.scalars(select(ExpenseDocument.expense_id).join(Expense).where(
            Expense.project_id==project.id,Expense.publication_status=='published',ExpenseDocument.publication_status=='published',
            ExpenseDocument.redacted_from_id.is_not(None),ExpenseDocument.approved_by.is_not(None),ExpenseDocument.approved_at.is_not(None))))
    for expense in published:
        key=expense.category.strip().casefold()
        categories.setdefault(key,dict(category=key,allocated_cents=0,reported_spending_cents=0))['reported_spending_cents']+=expense.amount_cents
        result=verification(db,expense,user) if private else dict(classification='document_attached' if expense.id in public_support else 'self_reported',supporting_document_count=int(expense.id in public_support),unresolved_discrepancy_count=None)
        bucket=coverage.setdefault(result['classification'],dict(classification=result['classification'],expense_count=0,amount_cents=0))
        bucket['expense_count']+=1;bucket['amount_cents']+=expense.amount_cents
        if result['supporting_document_count']:with_count+=1;with_amount+=expense.amount_cents
        if private and result['unresolved_discrepancy_count']:
            unresolved_expenses+=1;unresolved_count+=result['unresolved_discrepancy_count']
    for item in categories.values():
        item['remaining_cents']=item['allocated_cents']-item['reported_spending_cents']
        item['overspend_cents']=max(0,-item['remaining_cents'])
    spent=sum(e.amount_cents for e in published)
    return dict(project_id=project.id,currency=project.currency,audience='manager_private' if private else 'public_evidence_only',
                gross_completed_funding_cents=gross,refund_excluded_cents=refunds,reversal_excluded_cents=reversals,
                net_recorded_funding_cents=net,published_reported_spending_cents=spent,funding_minus_reported_expenditure_cents=net-spent,
                published_expense_count=len(published),expenses_with_documents_count=with_count,expenses_with_documents_cents=with_amount,
                expenses_without_documents_count=len(published)-with_count,expenses_without_documents_cents=spent-with_amount,
                unresolved_expenses_count=unresolved_expenses if private else None,unresolved_discrepancy_count=unresolved_count if private else None,
                evidence_coverage=[coverage[key] for key in sorted(coverage)],budget_variance=[categories[key] for key in sorted(categories)],
                calculated_at=db.scalar(select(func.transaction_timestamp())),notes=[
                    'Sandbox capture records are not a verified bank balance. Funding minus reported expenses is only a calculated difference.',
                    'Refund/reversal exclusions use original contribution amounts. Partial refund amounts are not stored; exact refund totals are unavailable.',
                    'Document/OCR support and human review do not certify vendor payment. Independently payment-matched evidence is not assigned.',
                    'Public evidence coverage includes only approved published redactions; private findings and reviewer notes are withheld.'])


def load_finding(db,finding_id,user):
    try:
        rid,digest=finding_id.split(':')
        UUID(rid)
        if len(digest)!=32 or any(c not in '0123456789abcdef' for c in digest):raise ValueError()
    except ValueError:raise HTTPException(422,'Invalid finding reference') from None
    record=db.get(ReceiptExtraction,rid)
    if not record:raise HTTPException(404,'Finding not found')
    doc=pipeline.managed_document(db,record.expense_document_id,user)
    expense=expenses.get(db,doc.expense_id,user,write=True)
    record=db.scalar(select(ReceiptExtraction).where(ReceiptExtraction.id==record.id).with_for_update().execution_options(populate_existing=True))
    selected=selected_records(db,[doc]).get(doc.id)
    if not selected or selected.id!=record.id:raise HTTPException(409,'Finding belongs to a superseded extraction')
    current=next((f for f in finding_views(db,record,expense,doc) if f['id']==finding_id),None)
    if not current:raise HTTPException(409,'Finding changed; refresh before reviewing')
    return record,doc,current


def review(db,finding_id,user,data):
    # Serialize with document/expense changes. Audit decisions never edit source data.
    existing=db.scalar(select(FindingReview).where(FindingReview.actor_id==user.id,FindingReview.request_key==str(data.request_key)))
    if existing:
        previous=db.get(ReceiptExtraction,existing.extraction_id)
        pipeline.managed_document(db,previous.expense_document_id,user)
        if existing.finding_reference!=finding_id or existing.action!=data.action or existing.field_name!=data.field_name or existing.reason!=data.reason:
            raise HTTPException(409,'Review request key already used for a different decision')
        return existing
    record,doc,finding=load_finding(db,finding_id,user)
    # Recheck after the parent lock for simultaneous same-key submissions.
    concurrent=db.scalar(select(FindingReview).where(FindingReview.actor_id==user.id,FindingReview.request_key==str(data.request_key)))
    if concurrent:
        if concurrent.finding_reference==finding_id and concurrent.action==data.action and concurrent.field_name==data.field_name and concurrent.reason==data.reason:return concurrent
        raise HTTPException(409,'Review request key already used')
    reference_fields=finding['evidence_reference'].get('fields',[])
    direct_field=finding['evidence_reference'].get('field')
    if data.field_name and data.field_name not in [direct_field,*reference_fields]:raise HTTPException(422,'Field does not belong to this finding')
    if data.field_name and (record.extracted_json or {}).get(data.field_name,{}).get('value') is None:
        raise HTTPException(422,'No extracted value exists for this field; explain or mark reviewed instead')
    if data.action=='request_retry' and (finding['finding_code']!='EXTRACTION_FAILED' or record.extraction_version!=pipeline.VERSION):
        raise HTTPException(409,'Only a failed current-version extraction can be retried; completed versions are immutable')
    row=FindingReview(id=str(uuid4()),extraction_id=record.id,actor_id=user.id,request_key=str(data.request_key),action=data.action,
                      field_name=data.field_name,finding_reference=finding_id,finding_snapshot={key:value for key,value in finding.items() if key not in ('review_status','resolved')},reason=data.reason,created_at=db.scalar(select(func.clock_timestamp())))
    db.add(row);expenses.commit(db);db.refresh(row)
    if data.action=='request_retry':
        # Audit is durable before entering the existing bounded request-driven worker.
        pipeline.process(db,pipeline.managed_document(db,doc.id,user),user,retry=True)
    return row


def reconciled_outcome(entry,latest,codes,expense):
    if not latest or latest.extraction_status!='completed' or not latest.extracted_json:
        return 'awaiting_reconciliation'
    code=entry.finding_snapshot['finding_code']
    if code in codes:return 'unresolved'
    receipt=ExtractedReceipt.model_validate(latest.extracted_json)
    comparisons={'AMOUNT_MISMATCH':('total_cents',expense.amount_cents),'CURRENCY_MISMATCH':('currency',expense.currency),
                 'VENDOR_MISMATCH':('vendor_name',expense.vendor),'DATE_MISMATCH':('document_date',expense.expense_date.isoformat())}
    if code in comparisons:
        name,reported=comparisons[code];field=getattr(receipt,name)
        value=field.value.isoformat() if name=='document_date' and field.value is not None else field.value
        return 'no_longer_detected' if value is not None and field.confidence=='high' and normalize(str(value))==normalize(str(reported)) else 'awaiting_reconciliation'
    if code.startswith('MISSING_'):
        field=getattr(receipt,code[len('MISSING_'):].lower(),None)
        return 'no_longer_detected' if field and field.value is not None and field.confidence=='high' else 'awaiting_reconciliation'
    if code=='POSSIBLE_ARITHMETIC_INCONSISTENCY':
        fields=[receipt.subtotal_cents,receipt.tax_cents,receipt.total_cents]
        return 'no_longer_detected' if all(f.value is not None and f.confidence=='high' for f in fields) and fields[0].value+fields[1].value-(receipt.discount_cents.value or 0)==fields[2].value else 'awaiting_reconciliation'
    if code in ('EXTRACTION_FAILED','CATEGORY_BUDGET_OVERRUN'):return 'no_longer_detected'
    # Absence of a weak/duplicate signal alone is insufficient to declare resolution.
    return 'awaiting_reconciliation'


def review_history(db,expense,user):
    expense=expenses.get(db,expense.id,user,write=True)
    records=db.scalars(select(ReceiptExtraction).join(ExpenseDocument).where(ExpenseDocument.expense_id==expense.id)).all()
    active=selected_records(db,db.scalars(select(ExpenseDocument).where(ExpenseDocument.expense_id==expense.id)).all())
    entries=db.scalars(select(FindingReview).where(FindingReview.extraction_id.in_([r.id for r in records])).order_by(FindingReview.created_at.desc(),FindingReview.id)).all() if records else []
    active_refs={}
    for doc_id,record in active.items():
        active_refs[doc_id]={f['finding_code'] for f in finding_views(db,record,expense,db.get(ExpenseDocument,doc_id))}
    record_map={r.id:r for r in records}
    result=[]
    for entry in entries:
        origin=record_map[entry.extraction_id];latest=active.get(origin.expense_document_id)
        outcome=reconciled_outcome(entry,latest,active_refs.get(origin.expense_document_id,set()),expense)
        result.append({**{key:getattr(entry,key) for key in ['id','extraction_id','actor_id','action','field_name','finding_reference','finding_snapshot','reason','created_at']},'outcome':outcome})
    return result
