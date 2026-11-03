"""Reproducible public financial reasoning evaluation; no live LLM required."""
import asyncio
import hashlib
import json
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError

from app.agent.contracts import AgentQuestion
from app.agent.financial_reasoning import FinancialPlan, render_financial
from app.agent.orchestration import AgentConfig, grounded, orchestrate
from app.agent.providers import ModelMessage
from app.agent.tools import EvidenceTools
from app.agent import limits
from app.models.funding import Contribution, WebhookEvent
from app.models.expense import Expense
from app.services.accountability import read_snapshot
from test_accountability import ac, contribution, receipt, verification, decision
from test_transparency import redacted, extra_expense
from test_agent_orchestration import Replay, calls

CASES = json.loads((Path(__file__).parent / 'data/financial_agent_evaluation.json').read_text())
FORBIDDEN = ['committed fraud', 'misused the money', 'stopped working', 'verified cash balance is', '999999999 EUR', 'payment is independently verified']


@pytest.fixture(autouse=True)
def reset_limiter(monkeypatch):
    monkeypatch.setattr(limits, 'limiter', limits.RateLimiter())


def ask(ac, question, mode='deterministic'):
    return ac.client.post(f'/api/projects/{ac.p.id}/agent/query', json={
        'project_id': ac.p.id, 'question': question, 'mode': mode})


def sources(ac, ledger=False):
    with read_snapshot(ac.db) as reader:
        tools = EvidenceTools(reader)
        return [tools.get_project_finances(ac.p.id)] + ([tools.get_project_expenses(ac.p.id)] if ledger else [])


@pytest.mark.parametrize('case', CASES, ids=lambda c:c['id'])
def test_evaluation_dataset(ac, case):
    seed = case['seed']
    if seed in ('full', 'partial'):
        contribution(ac, amount=10000 if seed == 'full' else 2000)
    if seed == 'refunds':
        for status, amount in [('completed', 2000), ('refunded', 3000), ('reversed', 4000)]:
            contribution(ac, status, amount)
    if seed == 'overrun':
        extra_expense(ac, amount_cents=12000)
    secrets = []
    if seed in ('documents', 'private'):
        original, extraction = receipt(ac)
        secrets = [original.id, extraction.id, original.storage_key, original.original_filename]
        if seed == 'documents':
            redacted(ac, original); redacted(ac, original)
        else:
            finding = verification(ac)['findings'][0]
            assert decision(ac, finding).status_code == 200
            secrets.append('Synthetic private review explanation')
    r = ask(ac, case['question'])
    assert r.status_code == 200, r.text
    result = r.json()
    assert result['answer_status'] == case['status']
    assert result['execution_mode'] == 'deterministic'
    for phrase in case['contains']:
        assert phrase in result['answer'], result['answer']
    for phrase in FORBIDDEN + secrets:
        assert phrase not in r.text
    finance = next(e for e in result['evidence_used'] if e['claim'] == 'finances')
    for field, expected in case['facts'].items():
        assert finance['value']['financial_summary'][field] == expected
    assert set(case['required_claims']) <= {e['claim'] for e in result['evidence_used']}
    for e in result['evidence_used']:
        digest = hashlib.sha256(json.dumps(e['value'], sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()
        assert e['citation']['projection_sha256'] == digest
        assert e['citation'] in result['citations']
        assert e['project_id'] == ac.p.id and e['visibility'] == 'public_active_projects'


def test_llm_multitool_financial_explanation(ac):
    contribution(ac)
    def final(messages):
        evidence = [json.loads(m['content']) for m in messages if m['role'] == 'tool']
        return ModelMessage(content=json.dumps({'financial_claims': [
            {'kind': 'funding_reconciliation', 'references': [evidence[0]['citation']['reference']]},
            {'kind': 'expense_support', 'references': [e['citation']['reference'] for e in evidence]}]}))
    provider = Replay([calls('get_project_finances', project_id=ac.p.id),
                       calls('get_project_expenses', project_id=ac.p.id), final])
    with read_snapshot(ac.db) as reader:
        result = asyncio.run(orchestrate(EvidenceTools(reader), AgentQuestion(project_id=ac.p.id,
            question='Compare recorded funding and public expense support.', mode='llm'), provider))
    assert result.execution_mode == 'llm', result.model_dump()
    assert result.diagnostics['turn_count'] == 3 and len(result.citations) == 2
    assert '2000 USD minor units' in result.answer and '1000 USD minor units' in result.answer


@pytest.mark.parametrize('alteration', ['amount', 'currency', 'percentage', 'fraud', 'cause', 'unknown_citation', 'no_finances', 'wrong_category', 'mixed_output'])
def test_invalid_financial_claims(ac, alteration):
    evidence = sources(ac, True)
    refs = [e.citation.reference for e in evidence]
    claim = {'kind': 'funding_reconciliation', 'references': [refs[0]]}
    plan = {'financial_claims': [claim]}
    if alteration in ('amount', 'currency', 'percentage', 'fraud', 'cause'):
        claim[alteration] = {'amount':999999999, 'currency':'EUR', 'percentage':99,
                             'fraud':'committed fraud', 'cause':'misused money'}[alteration]
    elif alteration == 'unknown_citation': claim['references'] = ['invented']
    elif alteration == 'no_finances': claim['references'] = [refs[1]]
    elif alteration == 'wrong_category': claim.update(kind='budget_variance', category='invented')
    else: plan['facts'] = []
    with pytest.raises((ValueError, KeyError)):
        grounded(json.dumps(plan), evidence, AgentConfig())


def test_validation_fallback_preserves_actual_mode(ac):
    def bad(messages):
        e = json.loads(messages[-1]['content'])
        return ModelMessage(content=json.dumps({'financial_claims': [{'kind':'refunds',
            'references':[e['citation']['reference']], 'amount_cents':999999999}]}))
    with read_snapshot(ac.db) as reader:
        r = asyncio.run(orchestrate(EvidenceTools(reader), AgentQuestion(project_id=ac.p.id,
            question='How much has been refunded?', mode='llm'),
            Replay([calls('get_project_finances', project_id=ac.p.id), bad])))
    assert r.execution_mode == 'deterministic' and 'fallback' in ' '.join(r.limitations)
    assert '999999999' not in r.answer and 'exact amount refunded is unavailable' in r.answer


def test_cross_project_and_private_exclusion(ac):
    other = extra_expense(ac, project_id=ac.other.id, description='OTHER_SECRET')
    original, extraction = receipt(ac)
    extra_expense(ac, publication_status='draft', description='DRAFT_SECRET')
    r = ask(ac, 'Which published expenses lack supporting documents?')
    for secret in ['OTHER_SECRET', 'DRAFT_SECRET', original.id, extraction.id, original.storage_key, 'extracted_json']:
        assert secret not in r.text
    a, b = sources(ac, True)
    with read_snapshot(ac.db) as reader:
        foreign = EvidenceTools(reader).get_project_finances(ac.other.id)
    plan = FinancialPlan.model_validate({'financial_claims':[{'kind':'expense_support',
        'references':[foreign.citation.reference,b.citation.reference]}]})
    with pytest.raises(ValueError): render_financial(plan, [foreign,b])
    ac.p.status = 'draft'; ac.db.commit()
    assert ask(ac, 'How much has been refunded?').status_code == 404


def test_duplicate_capture_webhook_and_no_financial_mutation(ac):
    c = contribution(ac)
    with pytest.raises(IntegrityError):
        with ac.db.begin_nested():
            ac.db.add(Contribution(id=str(uuid4()), user_id=c.user_id, project_id=c.project_id,
                tier_id=c.tier_id, checkout_key=str(uuid4()), amount_cents=c.amount_cents,
                currency=c.currency, reward_snapshot={}, status='completed', capture_id=c.capture_id,
                capture_key=str(uuid4())))
            ac.db.flush()
    ac.db.add(WebhookEvent(id='AGENT_EVENT',event_type='PAYMENT.CAPTURE.COMPLETED')); ac.db.commit()
    with pytest.raises(IntegrityError):
        with ac.db.begin_nested():
            ac.db.add(WebhookEvent(id='AGENT_EVENT', event_type='PAYMENT.CAPTURE.COMPLETED')); ac.db.flush()
    before = (c.status, c.amount_cents, ac.e.amount_cents, ac.db.scalar(select(func.count()).select_from(WebhookEvent)))
    r = ask(ac, 'What is the funding reconciliation?')
    assert '2000 USD minor units' in r.json()['answer']
    ac.db.refresh(c); ac.db.refresh(ac.e)
    assert before == (c.status, c.amount_cents, ac.e.amount_cents, ac.db.scalar(select(func.count()).select_from(WebhookEvent)))


def test_financial_source_unavailable(ac, monkeypatch):
    def missing(*args): raise HTTPException(404, 'missing')
    monkeypatch.setattr(EvidenceTools, 'get_project_finances', missing)
    assert ask(ac, 'How much has been refunded?').json()['answer_status'] == 'unavailable_source'


def test_paging_and_support_not_extrapolated(ac):
    # Approved originals and extraction versions never enter public coverage by themselves.
    for _ in range(51): extra_expense(ac, amount_cents=1)
    r = ask(ac, 'Which published expenses lack supporting documents?').json()
    assert r['answer_status'] == 'answered'
    assert 'across 52 expenses' in r['answer'] and 'only retrieved pages' in r['answer']
    assert len(next(e for e in r['evidence_used'] if e['claim'].startswith('expenses'))['value']['items']) == 50


def test_no_implicit_history_or_consistency(ac):
    for question in ['Are expense reports consistent with approved supporting evidence?', 'What changed between available reporting dates?']:
        assert ask(ac, question).json()['answer_status'] == 'insufficient_evidence'


def test_infrastructure_comparison(ac):
    from app.models.budget_allocation import BudgetAllocation
    allocation = ac.db.scalar(select(BudgetAllocation).where(BudgetAllocation.project_id == ac.p.id))
    allocation.category = 'Infrastructure'
    ac.e.category = 'Infrastructure'; ac.e.amount_cents = 12000; ac.db.commit()
    r = ask(ac, 'Is this project spending more on infrastructure than planned?').json()
    assert r['answer_status'] == 'answered'
    assert 'allocated 10000 USD minor units' in r['answer'] and 'overrun 2000 USD minor units' in r['answer']


def test_public_reads_never_query_private_receipt_tables(ac):
    from sqlalchemy import event
    from app.models.receipt_extraction import ReceiptExtraction, ExtractionAttempt
    from datetime import datetime, timezone
    original, current = receipt(ac)
    redacted(ac, original); redacted(ac, original)
    ac.db.add(ReceiptExtraction(id=str(uuid4()), expense_document_id=original.id,
        extraction_version='historic', extraction_status='completed', extracted_json=current.extracted_json))
    for _ in range(2):
        ac.db.add(ExtractionAttempt(id=str(uuid4()), extraction_id=current.id,
            triggered_by=ac.users[0].id, status='completed', started_at=datetime.now(timezone.utc)))
    ac.db.commit()
    statements = []
    def capture(conn, cursor, statement, parameters, context, executemany):
        statements.append(statement.lower())
    event.listen(ac.engine, 'before_cursor_execute', capture)
    try:
        r = ask(ac, 'Are expense reports consistent with approved supporting evidence?').json()
    finally:
        event.remove(ac.engine, 'before_cursor_execute', capture)
    assert r['answer_status'] == 'insufficient_evidence'
    assert 'across 1 expenses' in r['answer']
    assert not any(name in sql for sql in statements for name in ['receipt_extractions', 'receipt_extraction_attempts', 'finding_reviews'])


def test_partial_refund_exclusion_is_not_exact_refund_claim(ac):
    # Phase 2 only stores the capture's affected status, not a partial-refund amount.
    contribution(ac, 'refunded', 10000)
    r = ask(ac, 'How much has been refunded?').json()
    s = r['evidence_used'][0]['value']['financial_summary']
    assert s['refund_excluded_cents'] == 10000 and s['net_recorded_funding_cents'] == 0
    assert s['exact_refund_total_cents'] is None
    assert 'exclusions are not exact cash refund totals' in r['answer']


def test_empty_project_and_unavailable_category(ac):
    ac.p, ac.other = ac.other, ac.p
    r = ask(ac, 'Which published expenses lack supporting documents?').json()
    assert r['answer_status'] == 'answered' and 'across 0 expenses' in r['answer']
    assert ask(ac, 'Is this project spending more on infrastructure than planned?').json()['answer_status'] == 'insufficient_evidence'
