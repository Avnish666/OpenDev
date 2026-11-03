"""Verified financial explanations over public Phase 3 projections, never model arithmetic."""
import json
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.agent.contracts import AgentAnswer

FinancialKind = Literal['funding_reconciliation', 'refunds', 'budget_variance',
                        'expense_support', 'public_findings', 'consistency',
                        'missing_information', 'reporting_changes']

FINANCIAL_INTENTS = {
    'funding_reconciliation': ('How much recorded funding remains after reported expenses?',
                               'Why is the project running out of funds?',
                               'What is the funding reconciliation?'),
    'refunds': ('How much has been refunded?',),
    'budget_variance': ('Which budget categories are over budget?',
                        'Is this project spending more on infrastructure than planned?'),
    'expense_support': ('Which published expenses lack supporting documents?',),
    'public_findings': ('What discrepancies have been publicly disclosed?',),
    'consistency': ('Are expense reports consistent with approved supporting evidence?',),
    'missing_information': ('What financial information is missing?',),
    'reporting_changes': ('What changed between available reporting dates?',),
}


class FinancialClaim(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    kind: FinancialKind
    references: list[str] = Field(min_length=1, max_length=6)
    category: str | None = Field(default=None, max_length=100)


class FinancialPlan(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    financial_claims: list[FinancialClaim] = Field(min_length=1, max_length=6)


def render_financial(plan, evidence, max_chars=6000):
    """Values/relationships come from one authoritative public snapshot.

    The model supplies only a template kind, optional existing category, and exact
    current-request references. No amounts, currency, percentages or prose accepted.
    """
    by_ref = {e.citation.reference: e for e in evidence}
    used, paragraphs, limitations = {}, [], []
    statuses = []
    for claim in plan.financial_claims:
        sources = [by_ref[ref] for ref in claim.references]
        if any(e.visibility != 'public_active_projects' for e in sources):
            raise ValueError('Nonpublic financial source')
        finances = [e for e in sources if e.claim == 'finances']
        if len(finances) != 1:
            raise ValueError('One financial snapshot citation is required per claim')
        finance = finances[0]
        s = finance.value['financial_summary']
        if s['audience'] != 'public_evidence_only' or s['project_id'] != finance.project_id:
            raise ValueError('Invalid financial audience or scope')
        if any(e.project_id != finance.project_id for e in sources):
            raise ValueError('Cross-project financial citation')
        ledgers = [e for e in sources if e.claim.startswith('expenses:offset:')]
        if len(sources) != 1 + len(ledgers):
            raise ValueError('Unrelated source citation')
        if claim.kind in ('expense_support', 'consistency') and not ledgers:
            raise ValueError('Published expense citation is required')
        if claim.category is not None and claim.kind != 'budget_variance':
            raise ValueError('Category only applies to budget comparisons')
        currency = s['currency']
        money = lambda value: f'{value} {currency} minor units'
        parts = []
        status = 'answered'
        if claim.kind == 'funding_reconciliation':
            parts = [
                f"Gross recorded captured funding, including refund/reversal-affected captures: {money(s['gross_completed_funding_cents'])}.",
                f"Net eligible completed captured funding after conservative exclusions: {money(s['net_recorded_funding_cents'])}.",
                f"Published reported spending: {money(s['published_reported_spending_cents'])}.",
                f"Funding minus reported expenditure: {money(s['funding_minus_reported_expenditure_cents'])}.",
                'This calculated difference is not an independently verified cash or bank balance. '
                'A negative difference indicates a recorded funding gap, not its cause. The records do not establish why funds were spent or why funding is insufficient.',
            ]
        elif claim.kind == 'refunds':
            parts = [f"Recorded refund exclusions (full capture where exact totals are unknown): {money(s['refund_excluded_cents'])}.",
                     f"Original capture amounts excluded for reversal-affected contributions: {money(s['reversal_excluded_cents'])}.",
                     ('The exact amount refunded is unavailable. A partial refund conservatively excludes the entire affected capture where its cumulative total is unknown; exclusions are not exact cash refund totals.' if s.get('exact_refund_total_cents') is None else f"Authoritative recorded cumulative refund total: {money(s['exact_refund_total_cents'])}. This observation is not a live bank balance.")]
        elif claim.kind == 'budget_variance':
            rows = s['budget_variance']
            if claim.category is not None:
                rows = [row for row in rows if row['category'].casefold() == claim.category.strip().casefold()]
                if not rows:
                    raise ValueError('Unknown budget category')
            if not rows:
                parts = ['No published category allocation or spending rows are available.']
                status = 'insufficient_evidence'
            for row in rows:
                parts.append(f"Category {json.dumps(row['category'])}: allocated {money(row['allocated_cents'])}; "
                             f"published reported spending {money(row['reported_spending_cents'])}; "
                             f"budget remaining {money(row['remaining_cents'])}; overrun {money(row['overspend_cents'])}.")
            parts.append('Budget comparisons describe reported expenses, not verified vendor payments or explanations of spending choices.')
        elif claim.kind in ('expense_support', 'consistency'):
            parts = [f"Published reported spending with approved public document support: {money(s['expenses_with_documents_cents'])} "
                     f"across {s['expenses_with_documents_count']} expenses.",
                     f"Published reported spending without approved public document support: {money(s['expenses_without_documents_cents'])} "
                     f"across {s['expenses_without_documents_count']} expenses.",
                     'Each expense is counted once regardless of document count or extraction attempts. '
                     'No approved public support does not mean private supporting documents do not exist.']
            ids, seen = [], set()
            for ledger in ledgers:
                for item in ledger.value['items']:
                    if item['project_id'] != finance.project_id or item['currency'] != currency:
                        raise ValueError('Inconsistent public ledger scope/currency')
                    if item['id'] not in seen and not item['evidence']:
                        ids.append(item['id'])
                    seen.add(item['id'])
            parts.append('Expense IDs without approved public support in the retrieved pages: ' + json.dumps(ids) + '. '
                         'This list covers only retrieved pages; the amounts and counts above cover the full published snapshot.')
            if claim.kind == 'consistency':
                parts.append('Approved redacted documents are attached evidence only. Extraction-consistent, human-reviewed, '
                             'and private receipt-mismatch states are not publicly disclosed by the current publication policy. '
                             'Consistency cannot be established from these public records. No independent payment match is verified; a receipt does not prove a vendor was paid.')
                status = 'insufficient_evidence'
        elif claim.kind == 'public_findings':
            parts = [f"Public unresolved category budget-overrun findings: {finance.value['public_unresolved_discrepancy_count']}.",
                     'Disclosed categories: ' + json.dumps([row['category'] for row in finance.value['public_findings']]) + '.',
                     'These are comparisons of published category totals, not receipt-level allegations. '
                     'Private receipt findings and human-review notes are not published; this is not a count of all discrepancies and does not establish fraud.']
        elif claim.kind == 'missing_information':
            parts = ['Exact partial-refund amounts require authoritative cumulative observations; unknown historical amounts remain unavailable. Independently verified cash balances are unavailable. '
                     'Private receipt extractions, consistency determinations and reviewer notes are outside public scope. '
                     'No independent vendor-payment verification is available. '
                     'Published records do not establish completeness of all spending or external funding.',
                     f"Reported expenses without approved public document support: {s['expenses_without_documents_count']} "
                     f"totalling {money(s['expenses_without_documents_cents'])}."]
        else:
            parts = ['A historical reporting comparison cannot be established: these tools provide a current read-only snapshot, '
                     'not immutable dated financial snapshots. Expense dates and current update timestamps cannot reconstruct '
                     'previous budgets, contribution states, approvals or edited reports. No historical change amount is inferred.']
            status = 'insufficient_evidence'
        citations = ' '.join('[' + e.citation.reference + ']' for e in sources)
        paragraphs.append(' '.join(parts) + ' ' + citations)
        statuses.append(status)
        for e in sources:
            used[e.citation.reference] = e
            limitations.extend(e.limitations)
    text = '\n'.join(paragraphs)
    if len(text) > max_chars:
        raise ValueError('Financial explanation exceeds response budget')
    limitations.extend(['All amounts are integer minor units in the recorded project currency; no currency conversion or inferred percentage is provided.',
                        'Reported expenses and attached documents do not certify payment. Public category findings are not evidence of fraud.',
                        'Templates validate values and permitted relationships, not completeness, source truth, relevance or causal entailment.'])
    limitations.extend(f'{e.source_id}: freshness {e.freshness}; last update {e.last_updated_at}; retrieval {e.observed_at}.' for e in used.values())
    return AgentAnswer(answer=text, citations=[e.citation for e in used.values()], evidence_used=list(used.values()),
        limitations=list(dict.fromkeys(limitations)), confidence='limited_evidence',
        answer_status='insufficient_evidence' if 'insufficient_evidence' in statuses else 'answered')


def deterministic_financial(tools, question, kind):
    finance = tools.get_project_finances(question.project_id)
    sources = [finance]
    if kind in ('expense_support', 'consistency'):
        sources.append(tools.get_project_expenses(question.project_id))
    # The explicit infrastructure question narrows only to an authoritative category.
    category = 'infrastructure' if question.question.lower().strip().rstrip('?') == FINANCIAL_INTENTS['budget_variance'][1].lower().rstrip('?') else None
    if category and not any(row['category'] == category for row in finance.value['financial_summary']['budget_variance']):
        from app.agent.answers import result
        return result(finance, 'No published infrastructure category is available; spending cannot be compared with its allocation.', 'insufficient_evidence')
    claim = FinancialClaim(kind=kind, references=[e.citation.reference for e in sources], category=category)
    return render_financial(FinancialPlan(financial_claims=[claim]), sources)
