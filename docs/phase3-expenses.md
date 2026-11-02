# Phase 3 Step 1 — Expense Tracking Foundation

## Scope and financial meaning

This is an API/database foundation for **maintainer-reported** project expenses.
No receipt upload, document storage, AI extraction/approval, AG Studio, Bryntum,
frontend expense UI, or actual fund transfer is implemented. Payment logic is not
modified. The pre-existing Phase 2 review changes in this workspace are preserved.

Owners and authorized maintainers may record expenses on published projects
(active, paused, or completed). A positive funding balance is not required: reports
remain useful after refunds or for costs incurred before funding. Draft projects
must first be published. Existing GitHub session authentication and exact trusted
Origin checks protect every write. Ordinary collaborators and maintainers of
other projects cannot edit or publish a record.

Amounts are positive strict integer cents (booleans, floats and numeric strings are
rejected), bounded by PostgreSQL BIGINT. Currency is USD-only, consistent with the
existing project/reward APIs, and must match the project. The date is an ISO calendar
date, not proof of payment. Budget categories are not an allowlist: unforeseen
categories may be reported and appear with zero allocated budget.

`evidence_status` is server-controlled `unverified` and enforced in PostgreSQL.
Clients cannot set evidence status, project ID, submitter ID, publication state,
or timestamps in request bodies. There is no verification/approval API in this
step and no AI actor. Publication means a maintainer made the claim public; it
never establishes actual spending or a transfer. Vendor and description become
public when published, so maintainers should avoid personal or credential data.

## Files

Created:

- `backend/app/models/expense.py`
- `backend/app/schemas/expense.py`
- `backend/app/services/expenses.py`
- `backend/app/routers/expenses.py`
- `backend/migrations/versions/d488822839b2_add_reported_project_expenses.py`
- `backend/tests/test_expenses.py`
- `docs/phase3-expenses.md`

Modified only model registration in `backend/app/models/__init__.py` and router
registration in `backend/app/main.py`. Existing uncommitted Phase 2 review changes
were not reverted, committed, or extended with payment-processing changes.

## API and visibility

| Method | Path | Behavior |
| --- | --- | --- |
| POST | `/api/projects/{id}/expenses` | Owner/maintainer creates an unverified draft; returns 201. |
| GET | `/api/projects/{id}/expenses` | Published records only, even for managers, with `limit` (1–100, default 20) and `offset`. `include_drafts=true` is allowed only for that project's managers. Ordered by expense date descending, then ID descending. |
| GET | `/api/expenses/{id}` | Published record publicly visible; a draft is visible only to its project's managers; otherwise 404. |
| PATCH | `/api/expenses/{id}` | Owner/maintainer edits a draft; reject null fields, immutable fields and changes to published expenses. |
| POST | `/api/expenses/{id}/publish` | Publishes the draft; repeating publication is idempotent. Published records cannot be edited or unpublished through this API. |
| GET | `/api/projects/{id}/financial-summary` | Published expense totals, category budgets/variances, and contribution-based funding summary. No draft expense totals, including for managers. |

Public expense records/summaries remain visible for active, paused, and completed
projects; draft projects are hidden from non-managers. A draft project manager can
inspect its summary, but cannot create expenses until project publication.
There is no draft disclosure through another project's expense-list endpoint.

Example create body:

```json
{
  "category": "Development",
  "amount_cents": 2500,
  "currency": "USD",
  "vendor": "Example hosting provider",
  "description": "Maintainer-reported hosting expense",
  "expense_date": "2026-11-01"
}
```

Use the real signed-in session and an Origin exactly matching `FRONTEND_URL` for
POST/PATCH. Request bodies forbid unknown fields. Patching accepts any non-null
subset of these fields; it cannot reassign the project or submitting user.
Responses include IDs, server-controlled statuses and created/updated timestamps.

## Financial-summary rules

A single UNION ALL SQL statement reads budgets, published expenses and contributions
from one PostgreSQL statement snapshot. This avoids both inconsistent multi-query
snapshots and joins that multiply monetary totals. SUM(BIGINT) values are converted
to Python integers, never float. No payment provider is called.

- `completed_funding_cents`: project contributions with `status=completed`, a
  non-null capture ID and matching project currency. Pending, denied, cancelled,
  failed, refunded or reversed records do not count as available funded money.
- `excluded_refunded_or_reversed_cents`: original amounts of captured contributions
  currently marked refunded/reversed. **Phase 2 stores no partial-refund amount**;
  therefore even a partial refund conservatively excludes the whole contribution.
  This is explicitly identified in `refund_policy`; it is not an exact cash ledger
  or PayPal balance. No net-refund estimate is invented and payment logic is unchanged.
- `excluded_other_status_cents`: captured contributions in other non-completed
  statuses, such as pending/denied. Attempts without capture IDs are not funding.
- `excluded_currency_mismatch_count`: rows excluded for mismatched currency, rather
  than adding unlike monetary units.
- `reported_spending_cents`: sum of published expense claims only.
- `independently_verified_spending_cents`: **zero** in this foundation. Neither a
  submitted claim nor publishing it is independent evidence of a transfer.
- `allocated_budget_cents`: all project budget allocations, including categories
  without expense records.
- `budget_remaining_cents`: allocated budget minus published reported spending;
  negative means reported overspend. Per-category `overspend_cents` is max(0, spent
  minus allocated). `funding_less_reported_spending_cents` compares the two separate
  records; it is not a wallet balance or authorization to transfer money.
- Categories are grouped by stripped, case-folded names so `Development` and
  ` development ` compare against the same allocation. Unbudgeted categories get
  an allocation of zero. All queries isolate the requested project.

Funding accuracy depends on Phase 2 contribution/webhook reconciliation: a refund
not yet recorded there is not independently discovered by the expense summary.
No claim of independent spending verification is made.

## Migration and transactions

Revision `d488822839b2` follows `6527bb06f9b7`. Its upgrade only adds `expenses` and
three indexes, positive-amount/status/currency/nonempty-text constraints, and
RESTRICT foreign keys to projects and users. No old table or migration is modified.
The new revision explicitly refuses destructive downgrade; use a reviewed forward
migration. The model uses SQLAlchemy 2 typed mappings, DATE, BIGINT and timezone-
aware timestamps. Updated timestamps are maintained by SQLAlchemy writes.

Expense writes consistently lock the project before its expense row, then commit
atomically. They refresh locked records before editing, so publication and edits
serialize. Commit failures roll back the transaction, including a flushed INSERT;
there is no committed half-written expense. No destructive database operations
are needed for tests; fixtures use isolated databases and roll back their data.

## Local setup and verification

1. Activate the prepared `/workspace/opendev-env` or install
   `backend/requirements-dev.txt` into a Python 3.12 environment. No new package is
   needed for expenses.
2. Verify DATABASE_URL targets a local/test PostgreSQL database, never Neon. Review
   the new revision and run `alembic upgrade head` from `backend/` **only on that
   verified local/test target**. Production migration requires separate approval.
3. Start the existing FastAPI app with its normal configuration. Sign in through
   GitHub. Create an expense, inspect its draft as a manager, publish it, and verify
   anonymous list/detail/summary behavior. Submit invalid and cross-project writes
   and confirm 4xx responses without changes.
4. For integration tests, set both DATABASE_URL and TEST_DATABASE_URL to a migrated
   local `opendev_test_*` database. Run `python -m pytest -q` in `backend/` and
   `alembic check`. The prepared `/workspace/opendev-setup/test-step7.py` harness
   creates a fresh isolated local database and runs those checks for the whole app.
5. Run `npx tsc -b`, `npm run build`, and `npm run lint` from `frontend/`. The existing
   CI workflow installs the backend test requirements, starts PostgreSQL, migrates
   its isolated test database, and runs pytest; GitHub Actions itself is not invoked
   in this task.

Tests cover manager authorization, anonymous/CSRF rejection, cross-project access,
field/currency/amount constraints, draft/public visibility, immutable publication,
funding/refund exclusions, case-normalized categories, unbudgeted overspend, empty
summaries, database constraints, and rollback after a flushed insert.

No production secrets, Neon connections, production migrations, deployments,
commits, or pushes are used by this task.

## Validation results

- Full backend suite: **87 passed, zero failed/skipped** (39 expense cases and 48
  existing project/payment cases), using a newly created isolated local database.
- New migration applied successfully there; `alembic check` reports no pending
  model differences. No existing migration changed and no downgrade was executed.
- Frontend TypeScript checks, production build and Oxlint pass. Two pre-existing
  AuthContext warnings remain; backend TestClient has its existing HTTPX warning.
- Backend compilation and `git diff --check` pass. GitHub-hosted CI and live browser
  behavior were not run; there is no new frontend expense UI in this API step.
