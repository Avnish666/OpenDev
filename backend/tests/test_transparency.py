"""Anonymous public ledger contracts and privacy regression tests."""
import hashlib
from datetime import datetime, timezone
from uuid import uuid4
import pytest
from app.models.expense import Expense
from app.models.expense_document import ExpenseDocument
from app.services import documents
from test_accountability import ac, contribution, receipt, verification, decision


def path(ac, suffix='transparency'):
    return f'/api/projects/{ac.p.id}/{suffix}'


def public(ac, suffix='transparency', **params):
    ac.identity[0] = None
    result = ac.client.get(path(ac, suffix), params=params)
    assert result.status_code == 200, result.text
    assert result.headers['cache-control'] == 'no-store'
    return result.json()


def redacted(ac, original, approved=True, published=True):
    doc = ExpenseDocument(id=str(uuid4()), expense_id=original.expense_id, uploaded_by=ac.users[0].id,
        storage_key='receipts/PRIVATE_STORAGE_'+uuid4().hex, original_filename='SENSITIVE_FILENAME.png',
        detected_mime_type='image/png', file_size_bytes=5, sha256_hash=hashlib.sha256(uuid4().bytes).hexdigest(),
        redacted_from_id=original.id, publication_status='published' if published and approved else 'private',
        approved_by=ac.users[0].id if approved else None, approved_at=datetime.now(timezone.utc) if approved else None)
    ac.db.add(doc); ac.db.commit(); return doc


def extra_expense(ac, **changes):
    values = dict(project_id=ac.p.id, submitted_by_user_id=ac.users[0].id, category='Development', amount_cents=2000,
                  currency='USD', vendor='Second vendor', description='Another published report', expense_date=ac.e.expense_date,
                  publication_status='published')
    values.update(changes); row = Expense(**values); ac.db.add(row); ac.db.commit(); return row


def test_signed_out_active_visibility_and_contract(ac):
    data = public(ac)
    assert data['financial_summary']['audience'] == 'public_evidence_only'
    assert data['last_updated_at'] == data['financial_summary']['calculated_at']
    assert data['private_discrepancy_count'] is None
    row = public(ac, 'ledger')['items'][0]
    assert set(row) == {'id','project_id','currency','category','vendor','description','amount_cents','expense_date','updated_at',
                        'public_evidence_status','evidence','findings','independently_payment_matched'}
    assert row['amount_cents'] == 1000 and row['currency'] == 'USD'
    assert row['public_evidence_status'] == 'self_reported' and row['independently_payment_matched'] is False
    assert public(ac, f'ledger/{ac.e.id}') == row


@pytest.mark.parametrize('status', ['draft', 'paused', 'completed'])
def test_only_active_projects_even_for_owner(ac, status):
    ac.p.status = status; ac.db.commit()
    for suffix in ['transparency', 'ledger', f'ledger/{ac.e.id}']:
        assert ac.client.get(path(ac, suffix)).status_code == 404
    assert ac.client.get('/api/projects/99999999/transparency').status_code == 404


def test_draft_expenses_not_searchable_or_visible(ac):
    extra_expense(ac, vendor='DRAFT_SECRET', publication_status='draft')
    assert public(ac, 'ledger', q='DRAFT_SECRET')['total'] == 0
    ac.e.publication_status = 'draft'; ac.db.commit()
    assert public(ac, 'ledger')['total'] == 0
    assert ac.client.get(path(ac, f'ledger/{ac.e.id}')).status_code == 404
    assert public(ac)['financial_summary']['published_reported_spending_cents'] == 0


def test_authoritative_funding_and_refund_exclusions(ac):
    for status, amount in [('completed',20000),('refunded',3000),('reversed',4000),('pending',9900),('denied',9900),('failed',9900)]:
        contribution(ac, status, amount)
    contribution(ac, 'completed', 9000, capture=False)
    s = public(ac)['financial_summary']
    assert (s['gross_completed_funding_cents'],s['refund_excluded_cents'],s['reversal_excluded_cents']) == (27000,3000,4000)
    assert s['net_recorded_funding_cents'] == 20000 and s['funding_minus_reported_expenditure_cents'] == 19000
    assert s['exact_refund_total_cents'] is None and 'Partial refund' in ' '.join(s['notes'])


def test_budget_and_safe_public_findings(ac):
    extra_expense(ac, amount_cents=10000)
    data = public(ac)
    category = data['financial_summary']['budget_variance'][0]
    assert category['allocated_cents'] == 10000 and category['reported_spending_cents'] == 11000
    assert category['remaining_cents'] == -1000 and category['overspend_cents'] == 1000
    assert data['public_unresolved_discrepancy_count'] == 1
    assert data['public_findings'] == [dict(category='development',finding_code='CATEGORY_BUDGET_OVERRUN',severity='warning',
        explanation='Published reported spending exceeds the allocated category budget.',unresolved=True,scope='published_category_totals')]
    assert public(ac, f'ledger/{ac.e.id}')['findings'] == data['public_findings']
    assert public(ac)['financial_summary']['unresolved_discrepancy_count'] is None


def test_multiple_documents_coverage_and_evidence_filter(ac):
    original, _ = receipt(ac)
    a = redacted(ac, original); b = redacted(ac, original)
    redacted(ac, original, approved=False); redacted(ac, original, published=False)
    s = public(ac)['financial_summary']
    assert s['expenses_with_documents_count'] == 1 and s['expenses_with_documents_cents'] == 1000
    row = public(ac, 'ledger', evidence='supported')['items'][0]
    assert {d['id'] for d in row['evidence']} == {a.id,b.id}
    assert all(set(d) == {'id','detected_mime_type','status'} for d in row['evidence'])
    assert public(ac, 'ledger', evidence='unsupported')['total'] == 0


def test_originals_unapproved_and_ocr_never_disclosed_even_to_owner(ac):
    original, record = receipt(ac, code='failed')
    finding = verification(ac)['findings'][0]; decision(ac, finding)
    bad = redacted(ac, original, approved=False)
    responses = [ac.client.get(path(ac, suffix)).text for suffix in ['transparency','ledger',f'ledger/{ac.e.id}']]
    public(ac)
    responses += [ac.client.get(path(ac, suffix)).text for suffix in ['transparency','ledger',f'ledger/{ac.e.id}']]
    for body in responses:
        for secret in [original.id, record.id, original.storage_key, original.original_filename, bad.id,
                       bad.storage_key,bad.original_filename,'SYNTHETIC_TIMEOUT','Synthetic private review', 'processing_error_code','extracted_json']:
            assert secret not in body
    assert public(ac)['public_unresolved_discrepancy_count'] == 0  # not a claim private findings are absent


def test_private_download_denial_and_approved_redaction_reauthorization(ac, monkeypatch):
    original, _ = receipt(ac); approved = redacted(ac, original); unapproved = redacted(ac, original, approved=False)
    calls = []
    def signed(key, mime):
        calls.append((key,mime)); return 'https://example.test/short-lived'
    monkeypatch.setattr(documents.storage, 'signed_url', signed)
    public(ac)
    for doc in [original,unapproved]:
        assert ac.client.get(f'/api/documents/{doc.id}/download').status_code == 404
    assert calls == []
    result = ac.client.get(f'/api/documents/{approved.id}/download')
    assert result.status_code == 200 and result.json()['expires_in'] == 60
    assert calls == [(approved.storage_key,'image/png')]
    approved.publication_status = 'private'; ac.db.commit()
    assert ac.client.get(f'/api/documents/{approved.id}/download').status_code == 404
    assert len(calls) == 1


def test_pagination_sorting_search_literal_wildcards(ac):
    b = extra_expense(ac); c = extra_expense(ac, vendor='Literal %_ vendor')
    newest = public(ac,'ledger',limit=1)
    assert newest['items'][0]['id'] == c.id and newest['total'] == 3
    assert public(ac,'ledger',limit=1,offset=1)['items'][0]['id'] == b.id
    assert public(ac,'ledger',limit=1,sort='date_asc')['items'][0]['id'] == ac.e.id
    assert public(ac,'ledger',q='%_')['total'] == 1
    assert public(ac,'ledger',category=' DEVELOPMENT ',q='second VENDOR')['items'][0]['id'] == b.id
    assert public(ac,'ledger',offset=99)['items'] == []


@pytest.mark.parametrize('params', [{'limit':0},{'limit':101},{'offset':-1},{'sort':'bad'},{'evidence':'private'},{'q':'x'*201}])
def test_invalid_filters(ac,params):
    assert ac.client.get(path(ac,'ledger'),params=params).status_code == 422


def test_cross_project_isolation(ac):
    other = extra_expense(ac, project_id=ac.other.id, vendor='OTHER_PROJECT_SECRET', amount_cents=9000)
    assert 'OTHER_PROJECT_SECRET' not in str(public(ac,'ledger'))
    assert ac.client.get(path(ac,f'ledger/{other.id}')).status_code == 404
    assert public(ac)['financial_summary']['published_reported_spending_cents'] == 1000


def test_empty_project(ac):
    ac.p, ac.other = ac.other, ac.p
    data = public(ac)
    assert data['financial_summary']['net_recorded_funding_cents'] == 0
    assert data['financial_summary']['published_expense_count'] == 0
    assert data['financial_summary']['budget_variance'] == [] and data['public_findings'] == []
    assert public(ac,'ledger')['items'] == []


def test_public_endpoints_cannot_write(ac):
    ac.identity[0] = None
    for suffix in ['transparency','ledger',f'ledger/{ac.e.id}']:
        assert ac.client.post(path(ac,suffix),json={'amount_cents':1}).status_code == 405
    ac.db.refresh(ac.e); assert ac.e.amount_cents == 1000
