# Phase 2: Sandbox funding and reward fulfillment

## What changed

New backend files: `app/models/funding.py`, `app/schemas/funding.py`,
`app/services/paypal.py`, `app/services/funding.py`, `app/routers/funding.py`,
`tests/test_funding.py`, `requirements-payments.txt`, and migration
`6527bb06f9b7_add_sandbox_contributions_entitlements_.py`. Model metadata and router
registration extend `app/models/__init__.py` and `app/main.py`.

New frontend `src/pages/Funding.tsx` provides Sandbox checkout buttons, approval/
cancellation return pages, backer history, and maintainer fulfillment forms.
`Projects.tsx` embeds checkout/fulfillment; `App.tsx` adds history and return routes.
Existing GitHub authentication, project creation, and rewards are reused.

## API

All browser writes require the existing session and exact trusted Origin.

- `POST /api/funding/orders`: `{tier_id, checkout_key}` (UUID). Rejects extra fields,
  including frontend amounts. Returns contribution and Sandbox approval URL. Same
  user/key reuses its claim and provider request ID. Different tier with same key
  returns 409.
- `POST /api/funding/{uuid}/capture`: backer-only; reads the order, captures only an
  approved order, then verifies canonical order/capture data before granting rewards.
- `POST /api/funding/{uuid}/cancel`: backer-only advisory cancellation. Never grants
  rewards or overrides a verified payment. A later verified capture still reconciles.
- `GET /api/me/contributions?offset=0&limit=20`: current backer's contribution/reward
  snapshots, status, order/capture IDs, and entitlement fulfillment notes.
- `GET /api/projects/{id}/fulfillments`: owner/maintainer's completed contributions.
- `PATCH /api/funding/{uuid}/fulfill`: owner/maintainer only, `{note}`; records actual
  manual reward delivery against a verified entitlement. Does not send rewards itself.
- `POST /api/paypal/webhook`: no browser CSRF requirement; requires PayPal signature
  verification using the configured webhook ID and PayPal's verification endpoint.
  Payload limited to 256 KiB. Processing failure rolls back the event claim so
  PayPal redelivery can retry; duplicate IDs cannot grant twice.

## Safety and state

Only `https://api-m.sandbox.paypal.com` is used. Approval redirects are restricted
to HTTPS `www.sandbox.paypal.com`. Tokens/client secrets never enter responses,
frontend variables, logs, contribution snapshots, or event records. No raw webhook
payload or payer financial details are persisted.

Amount/currency come from the database tier; checkout snapshots benefits/name and
price. Unique user/checkout keys and contribution row locks prevent parallel local
writes; stable independent create/capture PayPal-Request-Id values cover ambiguous
provider failures. Order/capture IDs and entitlement contribution IDs are unique.
The only entitlement-creation branch is a matching canonical `COMPLETED` capture:
order ID, one purchase unit, custom contribution ID, configured merchant, currency,
exact amount, one bound exact-amount capture are checked server-side. Duplicate completion
or out-of-order pending/denied events never grant another entitlement. Refunds and
reversals revoke entitlements; they cannot undo manually delivered rewards.

All funding is to **one configured Sandbox merchant**. This is not escrow, a
marketplace payout implementation, or multi-merchant routing. USD-only rewards are
inherited from Phase 1. No real contributions are fabricated.

Quantity limits reserve capacity under a tier row lock. Reservations for abandoned,
failed, denied, and cancelled checkouts are conservatively retained; an expiration/
provider-reconciliation workflow is still needed to release them safely. This can
undersell limited tiers. Unpersisted create-order results are not retried after five
hours, to avoid replay outside PayPal's default six-hour idempotency retention.
An administrator must reconcile those uncertain orders before starting replacements.
No background reconciliation worker or stock-expiration job is included.

## APIMatic use and exact sources

Read `paypal-plan.md` for the reviewed contract, operation paths, source revisions,
and durable-claim mapping. The installed APIMatic PayPal Context Plugin 0.4.1 was
read at `/home/agent/.codex/plugins/cache/context-plugins/paypal/0.4.1/skills/python/`.
Its `python-integrate-paypal` and getting-started guidance informed the contract-first
plan and SDK inspection; authentication guided backend-only explicit credentials;
configuration/resilience guided Sandbox host selection, no implicit write retries,
durable local claims plus provider idempotency; error handling guided sanitized
provider errors; testing guided transport-level mocks and request assertions.

The available SDK 2.29 source/map was inspected at
`context-plugins/paypal-python-sdk@143e57f2a3729d7df3727386b8c9ddf023d9a5df`.
It has Orders methods but no required webhook verification controller. The
implementation deliberately uses **HTTPX REST**, not invented SDK methods. No
PayPal SDK is installed and no SDK-specific type-check claim is made.

Official PayPal OpenAPI specifications were read from
`paypal/paypal-rest-api-specifications@90e8041ffe02d80c452d2b476bedd59a8d219bdc`:
`checkout_orders_v2.json` for create/get/capture and approval links,
`notifications_webhooks_v1.json` for signature fields/SUCCESS verification, and
`payments_payment_v2.json` for canonical capture details. Public API docs:
https://developer.paypal.com/docs/api/orders/v2/ and
https://developer.paypal.com/docs/api/webhooks/v1/#verify-webhook-signature_post .
These REST wire contracts, not remembered SDK symbol names, govern the adapter.

## Setup and manual Sandbox flow (not executed here)

1. Use the existing backend Python environment; install
   `python -m pip install -r requirements-app.txt` from `backend/` if needed.
   For tests, use `requirements-dev.txt`. The old scientific `requirements.txt`
   is retained separately and is not the web application installation target.
2. Securely configure **backend-only** `PAYPAL_CLIENT_ID`, `PAYPAL_CLIENT_SECRET`,
   `PAYPAL_MERCHANT_ID` (the Sandbox business merchant ID), and `PAYPAL_WEBHOOK_ID`.
   Use credentials from a PayPal **Sandbox** REST app, never live credentials.
   Do not paste secrets in chat or put them in Vite variables.
3. Allow backend HTTPS egress to `api-m.sandbox.paypal.com` through environment
   settings. Browser checkout needs `www.sandbox.paypal.com`. No live PayPal host
   override exists. Do not bypass TLS or the configured cloud proxy.
4. Review migration 6527bb06f9b7 (three tables, indexes, foreign keys and uniqueness),
   then apply `alembic upgrade head` **only to a verified local/test database**.
   Existing migrations were not modified; production migration needs approval.
5. Set `FRONTEND_URL` to the actual frontend origin; set public `VITE_API_URL` to the
   backend. Use consistent same-site hostnames for session cookies. Start existing
   FastAPI/Vite processes. No PayPal secret or public client ID is needed in React,
   because approval uses the provider's HATEOAS redirect rather than JS SDK buttons.
6. In PayPal Sandbox app settings, register a publicly reachable HTTPS webhook URL
   ending `/api/paypal/webhook`. Subscribe to `PAYMENT.CAPTURE.COMPLETED`, `.PENDING`,
   `.DENIED`, `.REFUNDED`, and `.REVERSED`. Configure its real webhook ID in backend
   settings. Webhook simulator events may not correspond to real stored orders;
   use actual Sandbox buyer transactions for full integration validation.
7. Sign in as a backer, choose an active project's reward, select Back with PayPal
   Sandbox, and approve with a Sandbox personal buyer account (different from the
   Sandbox merchant). On return click Complete funding. Inspect history for the
   verified completed capture ID and one granted entitlement.
8. Replay the capture request and resend the real webhook from PayPal; verify one
   entitlement and one event record per ID. Cancel another checkout and confirm no
   entitlement. Test pending/denied through PayPal's documented Sandbox testing
   facilities or the mocked tests; a pending payment must not grant a reward.
9. Sign in as the owner/maintainer, enter actual fulfillment details, mark fulfilled,
   and confirm the backer sees them. Use the Sandbox dashboard to refund a payment;
   its signed event should revoke the entitlement. Check wrong signatures fail and
   unrelated users cannot capture or see another backer's history.

Live Sandbox/browser/webhook delivery remains **unverified**: credentials and public
webhook endpoint are not configured in this task. No production migration,
deployment, push, or live PayPal transaction was performed.

## Automated validation

Tests in `tests/test_funding.py` use HTTPX MockTransport for OAuth, order create/get/
capture, capture reads and webhook signature verification. Assertions check the
actual Sandbox host, Basic token exchange, database-derived amount and persisted
request IDs. PostgreSQL integration tests cover duplicate create/capture/webhooks,
exactly-one grant, pending/denied-to-completed transitions, cancellation, invalid/
missing signatures, mismatched amounts, failed-event rollback/redelivery, timeout
retry, history access, CSRF, fulfillment permissions, immutable snapshots, quantity
limits, refunds/reversals and no secret fields in responses.

Use a fresh local `opendev_test_*` database; set `DATABASE_URL` and
`TEST_DATABASE_URL`, apply migrations there, then run `python -m pytest -q` in
`backend/`. In the prepared cloud instance, the existing
`/workspace/opendev-setup/test-step7.py` harness creates such a fresh database,
checks migration drift and runs all tests. It does not use Neon.

Validation: **48 tests passed, zero failed/skipped**; migration upgrade and Alembic
check pass. Frontend `npx tsc -b`, build and lint pass, with two existing AuthContext
warnings. HTTPX TestClient has its existing deprecation warning. Concurrency is
protected with row locks/unique constraints; tests exercise sequential duplicate
redelivery, not a multi-process stress test. No automated browser run was performed.

Pre-deployment audit and remaining issues: see `docs/phase2-review.md`. Refund/
reversal event handling, pre-capture checks, worker execution, response schemas,
CI configuration, and frontend recovery were corrected during that review.
