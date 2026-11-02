# PayPal Sandbox contract and implementation plan

Use the existing FastAPI routers/services, SQLAlchemy session dependency, typed
models, trusted-Origin checks, and React session auth. Baseline: 20 tests pass.
No configured PayPal credentials: mocked automated tests now; live smoke is unrun.

## Client decision and verified sources

Use direct asynchronous HTTPX REST calls (already used by `services/github_auth.py`),
not SDK calls. APIMatic plugin 0.4.1's getting-started, integration, authentication,
configuration/resilience, error-handling, client initialization and testing guidance
informed contract-first design, sandbox selection, explicit credentials, durable
claims, provider idempotency and transport tests. Its SDK 2.29 source/map at
`context-plugins/paypal-python-sdk@143e57f2a3729d7df3727386b8c9ddf023d9a5df`
was inspected: it has Orders but lacks the required webhook verification controller.
No SDK symbols will be invented or used; SDK-specific signature/model rules do not
apply to this REST adapter. No SDK installation is needed.

PayPal official OpenAPI source: `paypal/paypal-rest-api-specifications` revision
`90e8041ffe02d80c452d2b476bedd59a8d219bdc`, files in `openapi/`:
checkout_orders_v2.json, notifications_webhooks_v1.json, payments_payment_v2.json.

## REST contracts

- Fixed host `https://api-m.sandbox.paypal.com`; no live-host override.
- POST /v1/oauth2/token: Basic client ID/secret, form grant_type=client_credentials;
  token remains server-side. OAuth flow appears in official specs' security schemes.
- POST /v2/checkout/orders: intent CAPTURE, one purchase_unit with amount currency_code,
  decimal value derived exactly from stored integer cents, custom_id contribution ID,
  configured payee merchant_id. PayPal-Request-Id persisted per contribution, Prefer
  return=representation. Approve using returned PayPal HATEOAS approve/payer-action
  redirect; return/cancel URLs are fixed from trusted FRONTEND_URL, not request input.
- POST /v2/checkout/orders/{id}/capture: persisted independent request ID; recover via
  GET order before retrying after ambiguous errors. Never trust callback status.
- GET /v2/checkout/orders/{id} and GET /v2/payments/captures/{capture_id}: verify order,
  custom_id, merchant, currency, amount, capture binding, final capture and status.
- POST /v1/notifications/verify-webhook-signature: auth_algo, cert_url, transmission_id,
  transmission_sig, transmission_time from PayPal headers; webhook_id from backend
  config; webhook_event parsed object. Accept verification_status SUCCESS only.
  Never fetch caller-supplied certificate URLs ourselves.
- Persist verified event IDs uniquely; canonical capture fetch handles pending,
  denied, completed, refunded and reversed states. Completion cannot be downgraded
  by stale pending/denied/cancel events. Refund/reversal revokes entitlement.

## Durable claims

| Write | Durable claim/refusal | Catch/recovery | Implementation |
| --- | --- | --- | --- |
| Create order | user + checkout key unique; contribution row lock | insert conflict returns same record; lock before provider call | funding.start, funding.create_order |
| Capture | contribution row lock, persisted capture request ID | same lock; GET order reconciliation before capture | funding.capture |
| Webhook | unique event ID, transactional insert | ON CONFLICT DO NOTHING; rollback permits redelivery on processing error | funding.webhook |
| Entitlement | contribution unique | contribution lock + unique database constraint | funding.reconcile |

All state writes are transactional. Ambiguous provider failures retain claims and
request IDs, never release stock for uncertain payments. Tier row lock reserves
limited quantity when initiating checkout; abandoned/cancelled checkouts retain
reservations pending future expiration reconciliation (safe underselling).
Snapshot reward benefits/name/price at checkout. No client amounts accepted.

## Scope and required reading

MUST read APIMatic python-getting-started, python-integrate-paypal,
python-authentication, python-configuration-resilience, python-error-handling,
python-testing, python-client-initialization (read during preparation). REST source
operations above are authoritative for wire contracts. SDK-specific workflows are
not applied as if this were an SDK integration.

Implement models/new migration, REST adapter, funding/fulfillment services and
routes, redirect checkout/history UI, mocked PostgreSQL/HTTPX tests, manual flow.
No production migrations, live payments, deployments, pushes, or secrets in frontend.
