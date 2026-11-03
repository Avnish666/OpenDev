# Phase 7 Step 3: deployment preflight

Assessment: 2026-11-04, Asia/Calcutta. **NO-GO for public deployment.** No production secrets, migrations, deployment, provider transactions, paid services, commits or pushes were used in this step. Configuration syntax and local tests cannot establish credential revocation or service acceptance.

## 1. Deployment architecture

One proposed Render Docker web service serves built React/Vite Community assets and FastAPI `/api` on the **same HTTPS origin**. Neon is external PostgreSQL; Supabase is private receipt storage; GitHub supplies OAuth; payment APIs remain fixed PayPal Sandbox. No actual Render hostname or infrastructure provisioning has been verified. Use `https://<service>.onrender.com` only as a format, not an assigned URL. Images default `APP_ENV=production` so omitting the environment cannot silently enable development feature defaults. Docker context is `.`, Dockerfile `deploy/Dockerfile`, health path `/api/health`, one Uvicorn worker, platform `PORT`, UID 10001 and root-owned readable code. Frontend `VITE_API_URL` is empty, so browser calls remain relative. The default context excludes Studio, Enterprise dependencies, history and environment files. No migrations/model downloads run at startup.

## 2. Repository preflight and files changed

Initial `main` HEAD: `c1e1a817f99f1c80a0acf15c57567efbe3c981f3` (`Phase 7 Step 2 done`); initial tree was clean. Step 2 PDFium, exact refund observations and migration `b7a200000001` are present. No prior migration or dependency lock was changed. Existing ignored/private files were preserved. Current Step 3 work is uncommitted.

Changes: both Dockerfiles, `backend/app/core/{deployment,features}.py`, `core/config.py`, `app/main.py`; receipt upload router and document/extraction services; payment start/capture service; agent orchestration; `backend/tests/test_deployment_preflight.py`; `backend/.env.example`; `scripts/release-container-smoke.py`, `scripts/deployment-capacity-smoke.py`; `deploy/environment-manifest.json`; this report and local capacity JSON; deployment/blocker documentation links.

Main `npm ls`, lock structure and clean `npm ci` within Docker validate the Community graph; its lock contains no Studio/Enterprise packages. Both builds/type configurations pass. The existing optional Studio install deliberately omits duplicate React peers; its standalone peer diagnostic does not establish a license problem or justify adding Enterprise to the main graph. No live environment/key paths are tracked; examples remain placeholders and historical exposures remain unresolved. Current source is scanned without reading historical credential values.

Hosted CI status lookup was attempted with the configured CLI and failed (exit 1); **existing hosted CI success is unverified**, not assumed. Local equivalents passed. No workflow logs or secret configuration were opened or printed. The workflow provisions synthetic PostgreSQL, installs pinned dependencies/OCR, migrates/checks and runs pytest plus frontend test/lint/build; it has no environment-dump step.

## 3. Configuration manifest

The complete machine-readable manifest is [`deploy/environment-manifest.json`](../deploy/environment-manifest.json). The table below describes operator inputs, image defaults and isolated build controls. Example formats contain no actual credentials. Database URL checks run during settings construction, before SQLAlchemy can construct an engine or produce a driver diagnostic; remaining startup validation runs in the FastAPI entry point before serving requests; **Alembic does not require unrelated OAuth/storage/payment credentials**. Errors contain variable names, not supplied values. Validation does not contact providers. Missing production settings, invalid HTTPS origin/callback, invalid port, unsupported database shape or external DB without TLS mode, bad storage formats, invalid agent ranges and wildcard proxy trust fail closed. All three release controls accept only exact `true`/`false`.

Production requires core provider settings even when new intake is disabled: existing downloads and verified webhook recovery still need them. Placeholder examples intentionally cannot start a real production service. Use operator secret injection, never build arguments or frontend secrets. Prefer verified database certificates/hostnames (`verify-full` with a trusted CA); minimum accepted TLS modes do not themselves prove hostname verification. LLM enablement validates URL/model syntax, not availability or rights.
| Name | Purpose | Secret | Required | Example format | Provider | Validation | Verification |
| --- | --- | --- | --- | --- | --- | --- | --- |
| APP_ENV | Select secure production behavior | No | Required | production | operator | Known environment; production enables startup checks | Verify Secure cookies and restricted defaults |
| DATABASE_URL | PostgreSQL connection | Yes | Required | postgresql+psycopg://<role>:<password>@<host>/<db>?sslmode=verify-full | Neon | PostgreSQL scheme/host/database; external hosts require TLS mode | Approved target, CA/hostname verification, db-health and revision |
| FRONTEND_URL | Exact public origin | No | Required | https://<service>.onrender.com | Render | HTTPS; no credentials/path/query/fragment/trailing slash | Login redirect, CORS and Origin tests |
| GITHUB_CALLBACK_URL | OAuth return URL | No | Optional; derived | https://<service>.onrender.com/api/auth/github/callback | GitHub/operator | Must match derived same-origin path exactly | Match registered callback, complete two-account HTTPS login |
| GITHUB_CLIENT_ID | OAuth application ID | No | Required in production even with intake disabled | <owner-provided value> | GitHub | Nonempty/non-placeholder; storage URL/bucket use existing strict format validation | Provider test-account checklist; never infer validity from syntax |
| GITHUB_CLIENT_SECRET | OAuth code exchange | Yes | Required in production even with intake disabled | <owner-provided value> | GitHub | Nonempty/non-placeholder; storage URL/bucket use existing strict format validation | Provider test-account checklist; never infer validity from syntax |
| PAYPAL_CLIENT_ID | Sandbox app ID | No | Required in production even with intake disabled | <owner-provided value> | PayPal Sandbox | Nonempty/non-placeholder; storage URL/bucket use existing strict format validation | Provider test-account checklist; never infer validity from syntax |
| PAYPAL_CLIENT_SECRET | Sandbox API authentication | Yes | Required in production even with intake disabled | <owner-provided value> | PayPal Sandbox | Nonempty/non-placeholder; storage URL/bucket use existing strict format validation | Provider test-account checklist; never infer validity from syntax |
| PAYPAL_WEBHOOK_ID | Expected webhook registration | No | Required in production even with intake disabled | <owner-provided value> | PayPal Sandbox | Nonempty/non-placeholder; storage URL/bucket use existing strict format validation | Provider test-account checklist; never infer validity from syntax |
| PAYPAL_MERCHANT_ID | Expected capture receiver | No | Required in production even with intake disabled | <owner-provided value> | PayPal Sandbox | Nonempty/non-placeholder; storage URL/bucket use existing strict format validation | Provider test-account checklist; never infer validity from syntax |
| SUPABASE_URL | Storage project endpoint | No | Required in production even with intake disabled | https://<project>.supabase.co | Supabase | Nonempty/non-placeholder; storage URL/bucket use existing strict format validation | Provider test-account checklist; never infer validity from syntax |
| SUPABASE_STORAGE_BUCKET | Private receipts bucket | No | Required in production even with intake disabled | <owner-provided value> | Supabase | Nonempty/non-placeholder; storage URL/bucket use existing strict format validation | Provider test-account checklist; never infer validity from syntax |
| SUPABASE_SERVICE_ROLE_KEY | Backend-only storage access | Yes | Required in production even with intake disabled | <owner-provided value> | Supabase | Nonempty/non-placeholder; storage URL/bucket use existing strict format validation | Provider test-account checklist; never infer validity from syntax |
| RECEIPT_PROCESSING_ENABLED | Allow upload and extraction | No | Optional | false | operator | Exact true/false; false by default in production, true in development/testing | 503 at guarded write paths; deterministic answer when model disabled |
| CHECKOUT_ENABLED | Allow new checkout and capture | No | Optional | false | operator | Exact true/false; false by default in production, true in development/testing | 503 at guarded write paths; deterministic answer when model disabled |
| LLM_ENABLED | Allow model modes | No | Optional | false | operator | Exact true/false; false by default in production, true in development/testing | 503 at guarded write paths; deterministic answer when model disabled |
| OLLAMA_BASE_URL | Model connection/identity | No | Required when LLM_ENABLED=true | http://<private-model-host>:11434 | owner-controlled inference | Provider URL/model validated without connecting at startup | Actual tools, model rights, privacy/injection and latency acceptance |
| OLLAMA_MODEL | Model connection/identity | No | Required when LLM_ENABLED=true | <reviewed tool-capable model> | owner-controlled inference | Provider URL/model validated without connecting at startup | Actual tools, model rights, privacy/injection and latency acceptance |
| PORT | Listen port | No | Optional; platform supplied | 10000 | Render | Integer 1..65535 | HTTP health and graceful shutdown |
| FRONTEND_DIST | Built static directory | No | Image-supplied | /app/frontend-dist | Docker image | index.html must exist when configured | Root, hashed asset and API route checks |
| FORWARDED_ALLOW_IPS | Trusted proxy senders | No | Optional | <verified proxy IPs/CIDRs> | Render/operator | Wildcard rejected in production; Uvicorn parses trusted peers | Verify spoof rejection and real peer quotas through edge; default loopback only |
| AGENT_MODE | Bound agent mode | No | Optional | deterministic | operator | deterministic, llm or auto; checked at production startup | Exercise bounded tool/timeout/refusal paths; LLM flag overrides requested mode |
| AGENT_MAX_TOOL_CALLS | Bound agent max_tool_calls | No | Optional | 6 | operator | Integer 1..6; checked at production startup | Exercise bounded tool/timeout/refusal paths; LLM flag overrides requested mode |
| AGENT_MAX_TURNS | Bound agent max_turns | No | Optional | 3 | operator | Integer 1..6; checked at production startup | Exercise bounded tool/timeout/refusal paths; LLM flag overrides requested mode |
| AGENT_TIMEOUT_SECONDS | Bound agent timeout_seconds | No | Optional | 30 | operator | Number >0..120; checked at production startup | Exercise bounded tool/timeout/refusal paths; LLM flag overrides requested mode |
| AGENT_MODEL_TIMEOUT | Bound agent model_timeout | No | Optional | 15 | operator | Number >0..60; checked at production startup | Exercise bounded tool/timeout/refusal paths; LLM flag overrides requested mode |
| AGENT_TOOL_TIMEOUT | Bound agent tool_timeout | No | Optional | 5 | operator | Number >0..15; checked at production startup | Exercise bounded tool/timeout/refusal paths; LLM flag overrides requested mode |
| AGENT_MAX_CONTEXT_BYTES | Bound agent max_context_bytes | No | Optional | 24000 | operator | Integer 4096..32000; checked at production startup | Exercise bounded tool/timeout/refusal paths; LLM flag overrides requested mode |
| AGENT_MAX_TOOL_BYTES | Bound agent max_tool_bytes | No | Optional | 12000 | operator | Integer 1024..24000; checked at production startup | Exercise bounded tool/timeout/refusal paths; LLM flag overrides requested mode |
| AGENT_MAX_RESPONSE_CHARS | Bound agent max_response_chars | No | Optional | 6000 | operator | Integer 500..8000; checked at production startup | Exercise bounded tool/timeout/refusal paths; LLM flag overrides requested mode |
| VITE_API_URL | Browser API base | No | Build setting | (empty) | Docker build | Public candidate fixes same-origin Community build; Studio directory excluded | Inspect bundle and relative API requests |
| VITE_ANALYTICS_RENDERER | Default public renderer | No | Build setting | community | Docker build | Public candidate fixes same-origin Community build; Studio directory excluded | Inspect bundle and relative API requests |
| PYTHONDONTWRITEBYTECODE | Image/runtime housekeeping | No | Image-supplied | 1 | Dockerfile | Fixed image defaults; OCR independently forces one OpenMP thread | Smoke build/start/OCR; not a secret or security sandbox |
| PYTHONUNBUFFERED | Image/runtime housekeeping | No | Image-supplied | 1 | Dockerfile | Fixed image defaults; OCR independently forces one OpenMP thread | Smoke build/start/OCR; not a secret or security sandbox |
| PIP_NO_CACHE_DIR | Image/runtime housekeeping | No | Image-supplied | 1 | Dockerfile | Fixed image defaults; OCR independently forces one OpenMP thread | Smoke build/start/OCR; not a secret or security sandbox |
| OMP_THREAD_LIMIT | Image/runtime housekeeping | No | Image-supplied | 1 | Dockerfile | Fixed image defaults; OCR independently forces one OpenMP thread | Smoke build/start/OCR; not a secret or security sandbox |
| ANALYTICS_STUDIO_EVALUATION | Optional isolated Studio build only | No | Never in public candidate | unset | local evaluator/vendor | Default build excludes optional installation; flags do not establish legal rights | Local evaluation only; no Studio SDK in Community lock/bundle |
| ANALYTICS_STUDIO_LICENSED | Optional isolated Studio build only | No | Never in public candidate | unset | local evaluator/vendor | Default build excludes optional installation; flags do not establish legal rights | Local evaluation only; no Studio SDK in Community lock/bundle |
| VITE_AG_STUDIO_LICENSE_KEY | Public-in-bundle vendor token, isolated licensed/evaluation build only | No | Never in public candidate | unset | local evaluator/vendor | Default build excludes optional installation; flags do not establish legal rights | Local evaluation only; no Studio SDK in Community lock/bundle |


`VITE_AG_STUDIO_LICENSE_KEY` would be visible in a licensed client build; it is not a backend secret and must be absent from this public Community candidate. Proxy/CA credentials supplied by the managed environment are not application manifest variables; do not copy them into images or logs. Test-only `TEST_DATABASE_URL` must target disposable local `opendev_test_*` databases, never Neon.

## 4. Owner-controlled credential rotation

Status: **owner verification required**. There is no confirmation that the historical database/GitHub OAuth values have been revoked. Preserve the redacted findings in `docs/phase7-credential-review.json`; do not extract or authenticate with historical values. Owner must identify the affected role/app, revoke genuine old credentials, create least-privilege replacements in provider UIs, update backend runtime settings, recycle affected connections, review access/activity and CI/artifacts/forks, and invalidate sessions if incident scope warrants it. Record owner, revocation timestamp/provider reference and sanitized acceptance evidence. If other categories were exposed, use their provider-supported key rotation. Deleting examples or passing the working-source scan does not revoke history. No automatic rotation/history rewriting occurred.

## 5. Migration and recovery runbook

Only disposable local PostgreSQL was used. Linear head remains `b7a200000001`, parent `8c6072dabc59`. Full tests include fresh installation, Phase 1 → payment-era → current-head preservation, original contributions/capture amounts and IDs, NULL historical refund totals, entitlement notes/status, event IDs, append-only triggers, sum/currency/binding constraints, monotonic totals, out-of-order events and concurrent replay. No existing revision changed. Invalid financial effects and webhook claims roll back together. Public analytics reads remain separate read-only snapshots.

Before any separately approved Neon migration: verify exact approved target/role and current revision privately; verify current free recovery retention; freeze writes and plan provider retries; create an access-restricted, encrypted/protected custom-format backup outside Git; checksum it; restore into a distinct **empty disposable** target and compare counts/amounts/IDs/entitlements/audits. A dump/list alone is not restore evidence. Use a protected libpq service file/secret binding, no passwords in command arguments or reports. Exact backup/restore commands and failure precautions are in [Step 2 migration runbook](phase7-deployment-preparation.md#migration-backup-and-recovery-runbook--manual-only).

After rehearsal and separate production approval, from `backend/` with the approved direct database URL securely injected (commands **not executed on Neon here**):

```sh
python -m alembic current
python -m alembic heads
python -m alembic upgrade b7a200000001
python -m alembic check
python -m alembic current
```

Post-migration read-only checks, in the approved application schema (compare protected baseline, not invented expected counts):

```sql
SELECT version_num FROM alembic_version;
SELECT status, currency, count(*), sum(amount_cents) FROM contributions GROUP BY status,currency;
SELECT status, count(*) FROM reward_entitlements GROUP BY status;
SELECT count(*) FROM paypal_events;
SELECT count(*) FROM paypal_refunds;
SELECT count(*) FROM contributions WHERE refund_total_cents IS NULL;
SELECT count(*) FROM contributions WHERE refund_total_cents < 0 OR refund_total_cents > amount_cents;
SELECT conname FROM pg_constraint WHERE conrelid IN ('contributions'::regclass,'paypal_refunds'::regclass);
SELECT tgname FROM pg_trigger WHERE tgrelid IN ('contributions'::regclass,'paypal_refunds'::regclass) AND NOT tgisinternal;
```

Expect head `b7a200000001`, preserved baseline records and zero out-of-bounds totals. Do not default unknown legacy refunds to zero or fabricate historical transaction IDs. New guards are `paypal_refund_guard` and `refunded_contribution_guard`. Test write rejection using synthetic records in rehearsal only. On failure keep traffic/writes paused, retain evidence and prefer a reviewed forward fix. Destructive downgrade is deliberately rejected. Restore only after explicit approval and reconciliation of post-backup payment activity; never restore stale financial state over active writes. The additive schema does not make an old binary's refund semantics safe for automatic rollback.

## 6. OCR containment findings

PDFium 5.14.0 wrapper/native build 156.0.8076.0, Pillow 13.0.0, pypdf 6.21.4 and English Tesseract are retained. Validation: 5 MiB upload, bounded streaming time, signatures/strict PDF traversal, reject encrypted/active/form/embedded content, ≤100 upload pages, ≤20 million image pixels. Extraction: ≤5 pages, native text/line/page/raster bounds, 320 MiB address space/50 CPU seconds/8 MiB file bound/60-second wall timeout; validator 256 MiB/5 CPU seconds/4 KiB output/8-second timeout. OCR: 12 seconds/page, one OpenMP thread, bounded TSV/results. Descriptor/core/no-new-privileges controls and process-group kill/drain/temp cleanup remain. Shared per-process admission prevents validation and extraction running together; a DB advisory transaction lock serializes extraction across instances. This is not global streaming admission/storage quota.

Whole-container local smoke enforces 512 MiB/one CPU/32 PIDs/read-only root/64 MiB noexec tmpfs/dropped capabilities/no-new-privileges/no network. These controls were tested locally, not on Render. Decoder and API still share UID, process visibility and normally network/filesystem permissions; resource limits are **not an exploit sandbox**. Public Render documentation was inaccessible, so a supported free-host per-job filesystem/proc/network/seccomp/cgroup boundary cannot be established. Do not assume privileged nested Docker, a Docker socket or namespace creation is available/safe there.

Explicit restricted candidate: `APP_ENV=production`, `RECEIPT_PROCESSING_ENABLED=false`, `CHECKOUT_ENABLED=false`, `LLM_ENABLED=false`. Receipt upload and extraction are backend-blocked, including authorized maintainer intake and redacted uploads; existing authorized reads remain. Direct owner-run decoder diagnostics are not a public bypass. Before enablement, verify a genuine OS boundary/hostile-load/ingress/storage quota plan on supported free infrastructure, or an approved isolated owner-controlled worker with no secrets/network and bounded files/processes. No completed functionality was removed; opt-in remains available after review. These controls do not close unrelated release gates or authorize even a restricted public launch.

## 7. PayPal Sandbox acceptance checklist — manual, not run

- Owner confirms rotated Sandbox app credentials, expected merchant and exact webhook registration; no live API host override is available.
- Authorized synthetic buyer tests approval/cancel, server-derived order amounts/currency/payee, retry with identical request keys, capture once, network/timeout ambiguity and recovery.
- Deliver real signature-verified completion, delayed pending/denied, duplicate/same-event and different-event/same-refund notifications; verify one financial effect and sanitized errors.
- Exercise multiple partial refunds, older cumulative observations, full-refund capture status, reversal before/after refunds, uncertain/missing cumulative fields, mismatched ID/currency/amount rejection and retry after provider failure.
- Compare authoritative Sandbox IDs/amounts to immutable observations and public aggregates; rewards revoke on refund/reversal without regrant on late completion; retain fulfillment notes. Pending/denied confer no rewards.
- Reconcile historical NULLs and abandoned limited-tier reservations with provider records; do not release stock based only on local age. Record observation coverage and manual recovery ownership.

Local mocked payment/constraint/race tests pass; no financial transaction occurred here. Checkout/capture disabled does not disable signature-verified webhook recovery, cancellation or history. Reconcile in-flight approvals before changing intake policy.

## 8. Supabase acceptance checklist — manual, not run

- Owner supplies backend-only service-role configuration and verifies a private bucket and project-specific quota/retention rules.
- Synthetic owner/maintainer uploads enforce size/content validation, unique server-generated object keys, no upsert and no caller-selected bucket/object paths. Unauthorized/cross-project writes and original-document public reads must fail.
- Test authenticated private download, authorized 60-second signed attachment URL, anonymous direct denial, expiry and residual validity until expiry; current authorization cannot retroactively revoke an already issued URL instantly.
- Publish only a distinct reviewed redaction tied to a published expense; inspect real hidden text, metadata and images. Approval is an attestation, not automatic true redaction.
- Exercise storage failures, ambiguous metadata commits, collision-safe cleanup, failed cleanup reconciliation, orphan/temp retention and safe retries. Original receipts remain private.

Adapter format/private-bucket/signing/cleanup tests pass locally. Actual bucket configuration, signed-link expiry and true redaction remain unverified. Restricted receipt intake does not establish safety of existing published evidence.

## 9. Authentication and browser security

Same-origin HTTPS origin must match GitHub registration and exact callback path. Production validation derives that callback only when omitted; an explicitly different origin/path fails. OAuth state is HttpOnly/Secure/Lax, 600 seconds and callback-path scoped. Random session tokens are hashed in DB and expire after seven days; production cookies are Secure/HttpOnly/Lax. Logout revokes the session; redirects use configured frontend origin. Browser writes require trusted Origin plus server authorization; CORS permits only that credentialed origin. Webhooks use verified provider signatures rather than browser CSRF. APIs retain no-store/no-referrer/nosniff and private/project masking.

Never disable CSRF or change SameSite to bypass cross-site hosting failures. Default proxy trust is loopback only; wildcard `FORWARDED_ALLOW_IPS=*` is rejected in production. Operator must establish real trusted edge IPs/CIDRs and spoof/cancellation behavior before relying on peer-based quotas. Actual HTTPS/two-account login/logout/cache/proxy/expiry acceptance remains required; local Chromium and cookie tests are not a live OAuth registration check. Suppress OAuth query codes in edge/access logs.

## 10. Resource measurements and Render comparison

See [local capacity JSON](phase7-step3-local-capacity.json). Production-mode no-network constrained OCR smoke: startup **9.16 s**, diagnostic processing **2.50 s**, maximum individual child RSS **63,116 KiB**, post-run idle container **68.53 MiB / 512 MiB**. The verified 512 MiB cgroup recorded a **176,676,864-byte (168.5 MiB) whole-container peak** across startup and this diagnostic workload; waited child CPU time was **2.02 seconds**. This includes the diagnostic process and is not worst-case hostile OCR or sustained peak throughput.

Separate testing-mode DB/static sample under 512 MiB/one CPU: startup **5.05 s**, static root 200/458 bytes, **20/20 database-health requests returned 200**, concurrency 8, median **29.93 ms**, maximum **91.12 ms**, **3 retained DB connections**, point CPU **0.20%**, post-run **69.8 MiB / 512 MiB**; graceful stop **0.56 s**, exit 0. CPU is an idle point sample, not peak OCR CPU or sustained throughput. Shared decoder/busy-request behavior is covered by kernel/admission tests; simultaneous worst-case upload/OCR/exports remain unmeasured. Local measurement uses synthetic PostgreSQL without TLS in testing mode; it is not production Neon TLS evidence.

`scripts/deployment-capacity-smoke.py` reproduces the sample against the existing local `opendev-phase7-postgres` fixture and a fresh named `opendev_test_*` DB, without dropping data. A reused DB name intentionally fails rather than overwrites. Docker smoke is reproducible with `python scripts/release-container-smoke.py --image opendev-review:phase7-step3`. Build with public proxy CA secret if required; do not disable TLS.

Current authoritative [Render Free](https://render.com/docs/free) and [Docker](https://render.com/docs/docker) documentation fetches failed; quota/terms/containment support cannot be verified. **Hosted capacity is unverified.** The local 512 MiB profile is a chosen test budget, not a current Render quota assertion. Owner must confirm current free memory/CPU/storage/request/cold-start limits and measure actual peak native load, DB pool saturation/wakeups, proxy behavior and recovery. Pool 3+2 overflow is per engine/worker, not global. Large lazy Community/Studio/Gantt bundles still require slow-network/mobile acceptance; actual build sizes and warnings are recorded below.


Bundle measurements (bytes and gzip bytes, exact artifacts in capacity JSON):

- Community `ProjectAnalyticsCommunity-Cn-gizuj.js`: 2,568,480 bytes / 732,073 gzip bytes.
- Community `RoadmapTimeline-CjAAWoip.js`: 1,946,819 bytes / 597,125 gzip bytes.
- Local Studio `ProjectAnalyticsStudioRenderer-Ddn4h8gk.js`: 5,278,018 bytes / 1,450,170 gzip bytes.

## 11. Feature flag behavior

Flags are backend settings, strict booleans read at process startup. Production defaults false; testing/development defaults true preserve the completed functionality and tests. Restart after changes. `CHECKOUT_ENABLED=false` rejects new orders and capture with 503; history/cancel/verified webhooks stay available. `RECEIPT_PROCESSING_ENABLED=false` rejects uploads before body consumption and service-level processing, and rejects extraction before any record/provider work; auth/project checks can still run. `LLM_ENABLED=false` forces deterministic evidence answers even when clients request `llm`/`auto`; it does not initialize a model. Existing UI request helpers display the server's unavailable message, and AI responses declare deterministic execution mode. Frontend flags cannot override server settings. Community's default build excludes Studio regardless of an unauthorized browser choice.

## 12. Automated verification

Full backend: **567 passed**, zero failed/skipped, 2 warnings, 337.83 seconds (552 preceding +15 new preflight cases). Full frontend: **87 passed**, zero failed/skipped/cancelled. Main/optional TypeScript, lint, Community and isolated local Studio evaluation builds pass. Lint has two existing AuthContext warnings; builds retain >500 kB chunk warnings. Backend warnings: Starlette HTTPX TestClient deprecation and synthetic pypdf `add_js` deprecation. No warning is treated as a skip/pass substitute.

Real PostgreSQL-backed Chromium: Community **1 passed/6 deselected**, 12.88 s; local Studio **1 passed/6 deselected**, 18.84 s, each with the existing deprecation warning. Trial banners confer no public rights. Default bundle/lock checks exclude Studio/Enterprise and backend-secret/database markers. Docker Community build and production-startup/OCR smoke pass with only synthetic provider settings. Fifteen configuration tests cover restricted defaults, derived callback, redacted errors, malformed flags/settings, no-side-effect disabled services and client inability to enable LLM access. No migration/dependency changes; fresh Alembic upgrade/check and historical financial/trigger preservation pass within full suite. Local and image dependency checks supplement lock review. Hosted CI remains unavailable.

Final Community image ID: `sha256:3a3b2a7cdae60d58e1eaf28a807e8f3eb086d726871dab8105b032ac09c91066`. An omitted production configuration was separately tested to exit nonzero with only the missing variable name in its diagnostic; image default is production. The API-only Dockerfile was also rebuilt/smoke-tested (`sha256:ab1c50ff1256387494555b02db70bb52526814a85aea6664c457709e49859604`). Actual production HTTP additionally verifies upload returns 503 while disabled and referenced hashed static assets return 200 where configured. These expected negative tests are not backend test failures.

## 13. Owner actions before any deployment

1. Verify credential revocation/rotation, access/CI/artifact incident scope and sanitized evidence; do not supply secrets in chat.
2. Approve application/contributor licensing and complete notices, including prior-artifact obligations. PDFium avoids new MuPDF AGPL, not all distribution obligations; Studio remains optional/unlicensed publicly.
3. Verify current free plans, TLS, backups/restores, host containment and global abuse/storage/traffic budgets. Keep restricted controls off until relevant evidence is approved.
4. Perform separately authorized live Sandbox, Supabase, actual HTTPS OAuth and private model acceptance with synthetic accounts/data. Resolve unknown refund coverage and limited-tier recovery policy.
5. Rehearse target schema and recovery, review exact artifact/digest/runtime manifest and owner release evidence. Obtain separate approval before commit/push, public hosting or production migration; keep automatic deployments disabled.

## 14. Remaining launch blockers

P7-01 credential revocation/incident verification; P7-02 application/legal/notice signoff; P7-03 true decoder containment/global quotas; P7-04 actual host/DB capacity and restore; P7-05 live HTTPS/proxy/logging/auth; P7-06 real Sandbox recovery; P7-07 historical exact refund coverage; P7-08 real private storage/redaction; P7-09 private model rights/connectivity/quality if enabled; P7-10 limited-tier reservations; P7-11 optional Studio rights; P7-12 beta/mobile/browser/bundle acceptance; P7-13 hosted CI/native/OS supply-chain review; P7-14 native spreadsheet import/re-save. Restricted flags reduce exposed operations but do not silently close these gates.

## 15. GO / NO-GO

**NO-GO for public deployment. GO for isolated remediation, operator review and synthetic preflight only.** Startup validation is configuration checking, not proof of provider credentials, revocation, legal rights, HTTPS behavior, sandboxing or free-tier capacity. No production deployment, migration, payment, automatic commit or push occurred.
