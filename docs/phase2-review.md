# Phase 2 pre-deployment review

Reviewed local source at base commit d30c70e on 2026-11-02. Read AGENTS.md,
`docs/phase2-paypal.md` including its manual Sandbox guide, and actual services,
routers, models, schemas, migration, frontend and tests. No production credentials,
production migrations, deployment, commit or push were used.

## Critical/high-priority findings and fixes

1. **Capture validated financial/order binding only after the charge (fixed).**
   `services/funding.py:validate_order` now checks the provider order ID, CAPTURE
   intent, single purchase unit, contribution custom ID, configured merchant, amount
   and currency **before** POST capture. Authentication/row ownership already
   restricted callers, but post-charge rejection was too late for a corrupt binding.
   New regressions assert a mismatch never sends a capture request.
2. **Refund-before-completion could grant a reward (fixed).** A signed refund could
   precede the canonical capture GET reflecting REFUNDED. Previously reconciliation
   saw COMPLETED, granted, then acknowledged the refund without revocation. Refund
   and reversal now explicitly suppress granting/revoke in the same transaction,
   after signature, capture identity and amount/binding checks. A later completion
   cannot restore revoked benefits. Tests cover stale canonical reads and event order.
3. **Blocking database waits inside async payment routes (fixed).** Concurrent
   requests could block the event loop waiting on a row/connection needed by an
   in-flight request. Checkout/capture now run as sync worker endpoints with async
   provider calls scoped inside that worker; webhooks delegate database/provider
   processing to the worker pool after bounded async body reading. A simulated
   lock-wait regression verifies the health endpoint remains responsive. This is
   not a multi-process database load test.
4. **Rollback data-loss hazard (operational restriction remains).** Migration
   6527bb06f9b7 `upgrade()` only creates new tables/indexes/constraints, but its
   `downgrade()` drops contributions, entitlements and events. Do not execute it.
   The already-applied migration was deliberately not edited. Use a reviewed
   forward migration for future schema corrections and prohibit automated downgrade.

## Medium-priority findings

- **Optional API field rejected legitimate captures (fixed).** PayPal's official
  payments schema declares `final_capture` optional, default false, and describes
  its meaning for authorization captures. Requiring it to be true for direct
  Orders CAPTURE was unsupported. Binding to a single exact-amount capture on a
  CAPTURE order remains enforced. A regression omits this field entirely.
- **Delayed terminal webhooks depended on the old Orders resource (fixed).** Refunds/
  reversals of an already bound capture now validate the canonical capture against
  the persisted trusted binding without needing the original order to remain
  available. New captures still need full order verification. A late-refund test
  makes GET order return 404 and confirms revocation.
- **CI was not running payment integration tests correctly (fixed configuration).**
  The legacy scientific requirements omit the web stack; TEST_DATABASE_URL and a
  PostgreSQL service were missing. New requirements-app/dev files preserve the old
  scientific list while CI installs web/test dependencies, provisions isolated
  PostgreSQL and migrates the test database. GitHub Actions itself has not been run
  here; dependency compatibility was checked in the prepared environment, not a
  new clean environment.
- **Frontend/API mismatches (fixed).** Maintainer response lacks github_id but was
  declared AuthUser; its type is now the exact public subset. History now exposes
  resume approval, clears stale errors, and return-page state remounts on route
  changes. Funding responses now have explicit Pydantic response schemas.
- **Abandoned limited-tier reservations never expire (remaining).** All contribution
  attempts count toward capacity, including cancellations, denials and failures.
  A test confirms cancelling a quantity-one checkout still blocks the next checkout.
  This safely avoids overselling but lets abandoned attempts exhaust availability.
  Do not enable limited-tier checkout broadly until a durable expiration/provider-
  reconciliation workflow exists. Browser cancellation alone is not safe evidence
  for releasing stock: an uncertain payment can still complete later.
- **Operational reconciliation remains manual.** No worker reconciles missing
  completion notifications, orphaned order claims, or repeatedly unknown event IDs.
  OAuth tokens are fetched for each API call rather than cached, increasing latency
  and rate-limit pressure. These need operational controls before wider use.

## Checklist evidence

| Check | Finding / verification |
| --- | --- |
| Database-only order amount | start snapshots tier price/currency, create uses that stored integer amount; request schema forbids amount fields. Existing tampering and snapshot tests pass. |
| OAuth and secrets | Fixed Sandbox host, backend Basic exchange, bearer used only server-side. No application logging statements or secret response fields. New provider-error test checks response/log sanitization; this does not audit external proxy/provider logs. |
| Capture ownership | Current user must own the locked contribution; full provider order checks now run before capture. Unrelated-user and mismatch tests pass. |
| API/database idempotency | Stable create/capture request IDs; unique user/key, order ID, capture ID, contribution entitlement, and event ID; row locks. Duplicate tests pass; no new migrations needed. |
| Webhook signatures | Verification endpoint must return SUCCESS before event insertion. Missing/invalid signature tests leave no event/entitlement. Failed processing rolls back for retry. |
| Delayed/duplicate/out-of-order | Completion followed by stale pending/denied, refund before completion, repeated event IDs, and expired-order refunds tested. |
| Exactly one reward | Only verified COMPLETED capture creates entitlement; unique contribution constraint plus row lock and duplicate completion tests. |
| Pending/denied | No grant; canonical transition to completed grants once. |
| Refund/reversal | Signed terminal event never grants; revokes existing entitlement; stale completion does not restore it. Manual delivered benefits cannot be recalled automatically. |
| Migration | Additive upgrade; destructive downgrade explicitly identified, unchanged and unexecuted. |
| Abandoned limited tiers | Retained reservation regression confirms remaining availability problem; no unsafe automatic release. |
| CSRF | Funding create, capture, cancel, fulfillment reject both absent and hostile Origin. Existing project/auth write routes reuse the same guard. Webhook relies on PayPal verification rather than browser cookies. |
| Frontend/backend schemas | TypeScript checks pass; public maintainer subset corrected and funding output schemas added; no browser E2E test suite exists. |

## Results and files

48 pytest cases passed, zero failed/skipped, on a fresh isolated local PostgreSQL
database. Migration upgrade and `alembic check` pass with no model drift.
TypeScript (`npx tsc -b`), frontend build, and Oxlint pass; two existing AuthContext
warnings and the existing TestClient HTTPX deprecation remain. No frontend runtime
unit/browser tests are configured. `pip install --dry-run -r requirements-dev.txt`
resolved against already installed dependencies; this is not clean-install proof.

Changed files:

- `backend/app/services/funding.py`
- `backend/app/routers/funding.py`
- `backend/app/schemas/funding.py`
- `backend/tests/test_funding.py`
- `backend/requirements-app.txt` (new)
- `backend/requirements-dev.txt` (new)
- `.github/workflows/ci.yml`
- `frontend/src/App.tsx`
- `frontend/src/api/client.ts`
- `frontend/src/pages/Funding.tsx`
- `docs/phase2-paypal.md`
- `docs/phase2-review.md` (this report)

Remaining work primarily affects the funding service/models and a new forward
migration for reservation lifecycle/reconciliation; do not alter old migrations.
Deployment build commands must use requirements-app.txt rather than the legacy
scientific requirements.txt. Live configuration and CI results still need review.

## Required manual Sandbox verification before deployment

Follow the guide in `docs/phase2-paypal.md`, using only Sandbox credentials and a
separate test database. Confirm actual approval/return URLs and same-site GitHub
session cookies in a browser; full create/approve/capture; cancelled checkout;
pending/denied behavior; backer-isolated history; owner/maintainer fulfillment;
real signed webhook delivery and resends; wrong signatures; refund/reversal before
and after completion; timeout recovery; and concurrent duplicate capture/webhook
requests. Inspect persisted contribution/capture/event/entitlement counts. Verify
limited-tier reservation exhaustion and the intended operator recovery policy.

A real HTTPS webhook endpoint and Sandbox business/buyer accounts are required.
Simulator-only events are insufficient to prove binding to actual stored orders.
Do not claim deployment readiness until these checks and reservation limitations
are addressed. No live Sandbox transactions were performed in this review.
