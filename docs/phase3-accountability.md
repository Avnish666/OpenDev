# Phase 3 Step 4 — Financial Accountability and Human Review

## Scope and files

Deterministic calculations over existing funding, budgets, published expense claims,
documents and extraction records. There is no LLM, paid API, fraud score, payment
certification, AG Studio integration, persistent aggregate cache or new payment flow.
Existing `Expense.evidence_status=unverified` and source extraction JSON remain unchanged.

Created:

- `backend/app/models/finding_review.py`
- `backend/app/schemas/accountability.py`
- `backend/app/services/accountability.py`
- `backend/app/routers/accountability.py`
- `backend/migrations/versions/a684112224e6_add_immutable_finding_review_audit.py`
- `backend/tests/test_accountability.py`
- `frontend/src/components/Accountability.tsx`
- `docs/phase3-accountability.md`

Modified model/router registration (`backend/app/models/__init__.py`,
`backend/app/main.py`) and `frontend/src/pages/Expenses.tsx` to embed financial cards,
budget variance, evidence coverage and private review controls. Existing uncommitted
Step 3 work is preserved; no PayPal processing logic or applied migration is edited.

## Financial computation rules

Snapshot endpoints run in a dedicated PostgreSQL **REPEATABLE READ, READ ONLY**
transaction. All funding, expense, evidence and review SELECTs see the same MVCC
snapshot, even if a concurrent writer records a refund or expense. No financial row
is updated by a snapshot. This uses another DB connection in addition to request
authentication; size connection pools appropriately for the free hosting runtime.

- Funding source is the existing contribution table. Require a non-null capture ID
  and the project's currency. Pending, denied, failed, cancelled and uncaptured
  records are never completed funding.
- `gross_completed_funding_cents` sums original capture amounts whose current status
  is completed/refunded/reversed (refund/reversal implies a preceding capture).
- `refund_excluded_cents` and `reversal_excluded_cents` sum original contribution
  amounts currently affected by those statuses.
- `net_recorded_funding_cents = gross − refund exclusions − reversal exclusions`.
  **Exact refund amounts are unavailable.** Phase 2 does not retain partial refund
  amounts; a partly refunded contribution is excluded in full. The response sets
  `exact_refund_total_cents=null` and explains this conservative limitation instead
  of presenting an invented refund amount or accurate provider balance.
- Capture IDs are unique in the existing database and defensively deduplicated in
  the calculation. Webhook events, receipts and attempts are never joined to the
  funding sum, so their multiplicity cannot inflate money.
- Reported spending includes only published expenses, matching the project's currency.
  Drafts never enter project totals, even for maintainers.
- Category keys are stripped/case-folded to match Step 1 rules. Allocation and
  published spending are summed separately; remaining = allocated − reported;
  overspend = max(0, reported − allocated). Unbudgeted categories have zero allocation.
- Funding minus reported expenditure is a **calculated difference**, not a wallet,
  escrow balance, verified bank balance or independently confirmed vendor payment.

There is one expense contribution to coverage/spending regardless of receipt count,
review count, extraction attempts or historical versions. Coverage amount buckets
are exclusive primary classifications, not overlapping totals to add together.
Unresolved issue counts deduplicate by **expense and finding code**; private detailed
findings retain separate source references for distinct receipts.

## Evidence classification and public privacy

Classification is computed, not written over existing evidence fields:

- `self_reported`: published/draft claim in its permitted audience.
- `document_attached`: visible supporting documents exist.
- `extraction_consistent`: private originals are processed, required vendor/date/
  currency/total fields have high extraction confidence, and current rules detect
  no finding. Confidence is not payment evidence.
- `discrepancy_detected`: a current receipt/processing issue needs review, including
  informational low-confidence issues.
- `human_reviewed`: an auditable human entry exists for selected extraction data;
  this means human engagement, not independent acceptance of financial facts.
- `independently_payment_matched`: reserved in the schema but **never assigned** by
  this implementation. No independent payment-matching channel exists.

An unresolved issue remains the primary classification even after a human accepts,
disputes or marks it reviewed. Otherwise the primary precedence is human-reviewed,
extraction-consistent, document-attached, self-reported. State lists are descriptive;
exclusive coverage buckets prevent amount double counting.

Current extractor version is preferred per original document; if absent, the latest
available extraction is selected. Historical versions/attempts do not add another
expense or another source of money. An unprocessed/failed original cannot be silently
ignored to call an expense fully extraction-consistent.

**Public audience:** only published expenses of active/paused/completed projects and
approved, published redacted evidence are visible. Private original IDs, OCR snippets,
findings, explanations, review history and reviewer opinions are not published.
Public discrepancy counts are **null/unavailable, not zero**; there is no automatic
publication channel for private findings or private-derived counts. Public coverage
uses approved public evidence only and labels that basis. Managers get private
coverage/findings and exact unresolved issue counts through the same authorized
snapshot endpoint. Independent-payment-matched amounts remain zero in both audiences.

## API contracts

| Method | Path | Behavior |
| --- | --- | --- |
| GET | `/api/projects/{id}/accountability` | Funding/spending reconciliation, category variance, audience-scoped coverage, unresolved counts (private only), calculation timestamp and caveats. |
| GET | `/api/projects/{id}/budget-variance` | Same snapshot calculation's category allocation/spending/remaining/overspend. |
| GET | `/api/expenses/{id}/verification` | Computed evidence state; manager-only detailed findings with stable references. Published expense public view contains approved document IDs only. |
| POST | `/api/extraction-findings/{finding_reference}/review` | Owner/maintainer human decision with existing authenticated session and exact trusted-Origin CSRF. |
| GET | `/api/expenses/{id}/review-history` | Owner/maintainer-only immutable audit entries and current reconciliation outcome. |

All responses use no-store/no-referrer. Draft project/expense reads are restricted
according to existing expense authorization. Ordinary collaborators, backers and
managers of other projects cannot review or read private history. No signing or
Storage network requests occur during accountability calculations.

Finding references are `extraction-UUID:content-digest`. The digest binds the code,
comparison values and evidence, not the mutable opinion overlay. They are returned
by the private verification API, not guessed from a numeric finding table. Stale
references return 409 if source comparisons changed or the version was superseded.

Example private review body:

```json
{
  "request_key": "8efc949e-5ff0-4b33-bc5a-e671ec2bb276",
  "action": "dispute_field",
  "field_name": "total_cents",
  "reason": "The OCR selected a value that needs further human inspection."
}
```

Actions: `explain`, `accept_field`, `dispute_field`, `mark_reviewed`, `request_retry`.
All need a 10–2000 character reason. Field decisions must name an identified value
belonging to that finding; unknown fields cannot be fabricated by accepting them.
Reasons/notes are private and must not contain credentials. Accept/dispute records
an opinion without changing an expense, transaction or original extraction.

Review submission keys are unique per actor. Replaying the same payload/key returns
its existing audit entry; changing the payload under a reused key returns 409.
Concurrent same-expense reviews serialize under existing project/expense locking,
then lock/reload the extraction to avoid accepting stale source data. Review rows
use the database clock after locking, so auth-transaction start time does not reorder
later human decisions.

`request_retry` is available for a failed current-version extraction. It durably
records the reason before invoking the existing bounded request-driven retry engine.
Completed extractor versions remain immutable: reprocessing completed data requires
a new extractor version rather than silent overwrite. Audited retry requests are
not a durable work queue; check the Step 3 state if a request is interrupted.

## Review outcomes and immutable audit

Migration **a684112224e6** follows 357405104f17 and adds **only `finding_reviews`**,
with extraction/actor FKs, unique submission key, action/reason checks and a lookup
index. A PostgreSQL trigger rejects UPDATE and DELETE of review entries. There are
no edit/delete audit APIs. The new migration refuses destructive downgrade. Existing
migrations are unchanged. Privileged DB administrators can bypass database controls;
use separate least-privilege runtime and migration roles operationally.

Stored actor, action, reason, field name, timestamp and frozen finding reference/
snapshot provide history. Later explanations append records rather than editing
older opinions. Current findings carry `reviewed`, `accepted` or `disputed` overlays
but **always remain unresolved while the rule still detects the issue**. Merely
marking a finding reviewed does not decrease unresolved totals.

History outcomes are computed from fresh reconciliation:

- `unresolved`: the same issue code is still detected on the selected source, even
  if its numeric values changed or a new extraction version was created.
- `no_longer_detected`: current reconciliation has sufficient supporting data to
  establish that the issue is absent. Field mismatches require a known,
  high-confidence value matching the current expense; arithmetic issues require
  high-confidence operands and a matching calculation. A correction uses the
  separate expense API. This is rule-level resolution, not vendor-payment
  certification.
- `awaiting_reconciliation`: processing is incomplete or current evidence cannot
  establish resolution. A missing/unknown replacement value, or the disappearance
  of a weak/duplicate signal, does not establish a correction.

There is intentionally no human `resolve` or `payment_verified` override action.
A reviewer cannot self-certify payment or erase contradictory receipt data.

## Frontend

The existing expense transparency section now includes net recorded funding,
published reported spending, budget/category variance, coverage and reconciliation
notes, with explicit public/private counts and last calculation time. Large values
outside JavaScript's safe integer range are not silently displayed as exact amounts;
server calculations remain exact integers.

Maintainers get private expense verification, finding-linked explanation/accept/
dispute/review/retry forms and immutable history. Refresh controls update current
snapshot/finding state. The UI makes human review, supporting documents and
independent payment evidence distinct; no "fraud detected" or bank-balance badge
is introduced. Existing extraction and redaction interfaces remain in use.

## Testing and manual verification

Tests use migrated isolated local schemas with committed fixtures so independent
read transactions and writer sessions see realistic PostgreSQL behavior. No Neon
or production connection is used. Tested scenarios cover completed/pending/denied/
failed funding, refund/reversal exclusions, duplicate capture/event constraints,
category variance, multiple receipts/versions, low-confidence findings, review
permissions and cross-project denial, append-only DB enforcement, private/public
boundaries, draft visibility, idempotency, concurrent ledger updates under repeatable
reads, concurrent review submissions and no source financial/extraction mutations.

Use the existing local test harness `/workspace/opendev-setup/test-step7.py`, or
set DATABASE_URL and TEST_DATABASE_URL to a fresh local `opendev_test_*` database,
apply migrations there, then run pytest and `alembic check` from backend. Frontend
checks: `npx tsc -b`, `npm run build`, `npm run lint`. Tesseract dependencies remain
those documented in Step 3. No new package is required for Step 4.

Validation results for this implementation:

- Backend suite: **153 passed, 0 failed, 0 skipped**, including 16 new accountability
  tests and all 137 preceding tests. One existing Starlette/HTTPX deprecation warning.
- Fresh local PostgreSQL migration to head and `alembic check`: passed.
- Frontend TypeScript checks, production build and lint: passed. Lint reports two
  existing AuthContext warnings.
- `git diff --check` and Python compilation: passed.

These are local checks, not a claim of hosted CI, live storage/provider integration
or browser end-to-end verification.

Manual checks before any deployment:

1. Review the new audit migration and apply only to a verified local/test database.
2. Use synthetic Sandbox contribution statuses and published/draft expenses; verify
   gross/exclusion/net formulas and category variances against the actual stored rows.
3. Attach multiple receipts and process several versions; check one expense/amount
   contribution to coverage and compare private findings with public redacted coverage.
4. As owner/maintainer, explain, accept, dispute and mark a finding reviewed; confirm
   the reason appears in immutable private history and unresolved counts remain.
5. Correct a draft through its existing explicit expense edit API, refresh, and
   inspect `no_longer_detected` history without any payment-verified status.
6. Retry a failed extraction through review; inspect both the audit and Step 3
   attempt records. Do not expect automatic retry after a disconnected request.
7. Compare anonymous/backer/collaborator/other-project access. No private snippets,
   original document IDs or notes may appear in public responses.
8. Test simultaneous review submissions and record updates on the deployed database
   pool configuration, with no production financial data.

Remaining limitations: exact partial-refund amounts and independent bank/vendor
payment evidence are unavailable; public disclosure of private-derived findings
requires a future explicit publication policy. Calculations are uncached and can
be expensive on large projects (private per-receipt checks perform several queries).
Monitor/rate-limit before broader use; a batched implementation/cache may be justified
later. Immutable snapshots can retain private snippets/reasons, so production privacy
and retention policies must account for audit records. No live Supabase/Render/
browser verification, production migration, deployment, commit or push is performed.
