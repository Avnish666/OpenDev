# Phase 7 Step 4: provider acceptance preparation and evidence

Assessment: 2026-11-04, Asia/Calcutta. **Public deployment remains NO-GO.** No production secrets, public hosting/tunnel, production migrations, real-money payments, provider refunds, provider objects, paid service, feature enablement, commit or push occurred. A failed/unavailable live check is not converted into a mocked success.

## 1. Repository state and preservation

Initial branch `main`, HEAD `dc9006ae8350da38d9d63fefaa8030bd97ab530b` (`Phase 7 Step 3 done`), working tree clean. Contrary to the request's historical note, Step 3 was already committed/pushed before this task. Actual Step 3 startup validation, production-default disabled controls, redacted database prevalidation and environment manifest are present. Existing files were preserved; initial/final whitespace checks pass. No prior migrations, manifests/dependency pins or financial formulas were changed.

Changed files: new `backend/app/acceptance/{__init__,providers,fixtures}.py`; `scripts/provider-acceptance.py` and `scripts/provider-fixtures.py`; `backend/tests/test_provider_acceptance.py`; narrow PayPal link validation in `backend/app/services/{paypal,funding}.py`; this report; readiness/network/local OCR JSON evidence and blocker-register amendment. Production controls are unchanged.

## 2. Test environment architecture and evidence classes

| Evidence class | What ran | What it establishes |
| --- | --- | --- |
| Mocked external integration | HTTPX MockTransport PayPal/Supabase tests, including new bounded/redirect/error cases | Application behavior against synthetic contracts, not provider acceptance |
| Local application/native integration | Disposable local PostgreSQL 16, real PDFium/Tesseract, synthetic files, cookie/permission/refund tests and Chromium | Local DB/authorization/OCR behavior; external providers still mocked |
| Live external provider | Unauthenticated fixed-host PayPal HEAD probes; no authenticated provider checks | Probe returned unavailable; no OAuth/account/bucket verification |
| Genuine staging webhook end-to-end | Not run; no verified reachable endpoint | Blocked; local replay/simulator fixtures are not genuine transaction deliveries |

No dedicated disposable acceptance credential variables are configured. The standalone harness imports neither application configuration nor dotenv and never falls back to application credentials. It reports production/application **presence by membership only**, not secret values or validity. Explicit feature values are reported only as `true`/`false`; absent/invalid values are labeled unknown rather than leaking input. This host's readiness output is not the effective settings of a separately configured deployment. The production images' disabled defaults were verified in Step 3.

Artifacts: [dry-run readiness](phase7-provider-readiness.json), [network probe](phase7-provider-network.json), [controlled local OCR](phase7-controlled-ocr-results.json). Network reachability is scoped to each attempted host, not a claim that all external networking is unavailable. Supabase was not probed because no disposable project reference was supplied. Existing managed network policy was respected; no TLS verification was disabled or policy bypass attempted.

## 3. PayPal Sandbox acceptance matrix

All financial/state tests below use **mocked provider responses with real local PostgreSQL**. Real provider status for every row is **not run/blocked** until the named owner prerequisites are satisfied.

| Case | Local evidence | Real acceptance required |
| --- | --- | --- |
| Business merchant/Personal buyer | Configuration shape and expected payee validation tested | Owner verifies distinct Sandbox Business merchant and Personal buyer; never real accounts |
| Order create/approval/capture | Server-derived amount/currency/custom ID, approval host, stable request keys, completed capture and one entitlement | Authorized buyer approves actual Sandbox order; compare provider order/capture to contribution |
| Genuine signature | Required signature headers, fixed Sandbox verification API, SUCCESS-only processing; invalid signatures rejected | Real delivery with matching Sandbox app/webhook ID and verification API result |
| Duplicate/out-of-order events | Event ID claim, refund ID dedup, row locks, rollback and reversal precedence tested | Resend genuine event; compare state/entitlement/observations before and after |
| Capture/webhook race | New two-session concurrent capture and completion-webhook test yields one captured contribution/one entitlement | Real approved Sandbox flow with overlapping app capture and genuine completion notification |
| Invalid signature/attribution | Mocked bad signatures, wrong order/merchant/amount and malformed resource links fail without a committed event claim | Authorized negative replay of a synthetic Sandbox event; no raw body/header tokens in report |
| Multiple partial/full refunds | Immutable IDs/amounts, cumulative monotonic totals, full-capture status, sum bounds, currency/precision/replay tests | Separately authorized owner performs Sandbox refunds manually; reconcile actual IDs/cumulative amounts |
| Reversal | Refund/reversal ordering and no double subtraction/regrant tested | Owner uses an officially supported Sandbox reversal scenario if available; otherwise remains unverified |
| Historical unknown totals | NULL remains unknown and conservative full exclusion persists | Reconcile only authoritative provider records; never synthesize historical amounts/IDs |
| Rewards/limited tiers | Grant once, fulfill, revoke on refund/reversal, pending/denied excluded, reserved capacity retained | Check actual eligibility/history and safe stock reconciliation; no time-only abandoned reservation release |

The harness can verify **Sandbox OAuth only**. A passed OAuth check does not prove merchant attribution, buyer approval, capture, webhook signatures or financial correctness. It never issues orders, captures, refunds or reversals. Existing application financial processing remains Sandbox-only. Checkout/capture stays disabled in production; signed webhook reconciliation remains available for existing state. Do not enable public checkout merely to produce a green acceptance result.

## 4. Supabase acceptance matrix

| Case | Local/mocked evidence | Disposable live procedure/status |
| --- | --- | --- |
| Private bucket | Existing adapter requires public=false; new probe checks exact bucket ID/private flag | GET test bucket metadata only when explicitly configured; not run here |
| Valid PDF/PNG/JPEG | Signature validation, upload metadata and four generated native/OCR fixtures pass locally | Upload **synthetic** files only through authorized isolated test workflow; not run |
| Size/MIME/image/page limits | Bounded upload streaming, invalid signatures, huge image header, >5 MiB and page-limit rejection | Verify provider bucket limit/types plus application limits separately; not run |
| Ownership/cross-project | Owner/maintainer checks, collaborator/outsider denial, generated object keys and no upsert covered in PostgreSQL tests | Use two projects/users and verify no cross-project document/signing access; not run |
| Anonymous/direct access | Mocked private-bucket checks; public API exposes approved redactions only | After authenticated retrieval succeeds, require anonymous public URL denial for that existing object; not run |
| Signed attachment URL | Exact bucket/key prefix, attachment naming, 60-second signing request and authorization tested | Immediate retrieval, then real expiry while object still exists; not run |
| Missing/failed upload | Mocked not-found, HTTP/network failures, collisions, uncertain commit and cleanup reconciliation | Use disposable synthetic object; record sanitized failure and metadata/object outcome; not run |
| Redaction | Distinct approved redaction relationship and private-original exclusion tested | Inspect hidden text/metadata/pixels; approval is not automatic true redaction; not run |
| Cleanup | Local temp fixtures auto-clean in tests; application cleanup failure path tested | Delete only IDs/keys created by that acceptance run, never whole buckets; not run |

A private metadata flag is not proof of RLS/object policy safety. A service-role key bypasses policies; keep it backend-only and test anonymous/user boundaries separately. Signed URLs are bearer credentials: do not put them, cookies, service-role keys or raw headers in logs, Git or acceptance reports. Do not mislabel a 404 after deleting an object as token expiry. Prove the object still exists through an authenticated fresh read/new URL after the original URL expires. Cleanup should occur **after** that test.

## 5. Controlled OCR acceptance results

The generator creates a new mode-0700 local directory and refuses to overwrite an existing directory. It produces nine synthetic files and a filename/size/hash manifest; it never reads a real receipt, uploads or edits provider objects. Valid contents explicitly say Synthetic Hosting, fixed synthetic invoice/date, USD and total 1234 minor units.

| Fixture | Actual local result |
| --- | --- |
| text.pdf | Real PDFium text extraction, total 1234 |
| scan.pdf | Real bounded raster/Tesseract extraction, total 1234 |
| receipt.png / receipt.jpg | Real image/Tesseract extraction, total 1234 each |
| corrupt.pdf | Rejected by real validator |
| six-pages.pdf | Structural upload may be valid; extraction rejects PAGE_LIMIT (five-page extraction cap) |
| large-image.png | Huge dimension header rejected without allocating a huge image |
| invalid.png | Invalid signature rejected |
| oversized.pdf | Local validator rejects; HTTP upload has an independent streamed 5 MiB/413 limit |

`phase7-controlled-ocr-results.json` records the actual local outcomes. Temporary files used for this run were scoped to an owned TemporaryDirectory and cleaned automatically. Existing suites cover OCR timeout/process-group kill, core/descriptor/CPU/address-space/output limits, shared admission, concurrent rejection, hashes/MIME recheck, stale leases, deterministic discrepancies and private human review/public redaction. A receipt alone is not proof of payment; mismatches require human review and do not establish fraud.

Production receipt intake and extraction remain disabled. These tests do not enforce a new OS boundary between decoder and API; UID/process visibility/filesystem/network separation, ingress/storage quotas and target-host hostile-load acceptance remain open.

## 6. Scripts, reproducible commands and cleanup

Use the pinned backend environment. Readiness requires explicit selection and defaults to no network:

```sh
# repository root; does not load application .env or contact providers
python scripts/provider-acceptance.py --environment disposable-test --dry-run
# bounded public-host probe only, no authentication, no Supabase host without test ref
python scripts/provider-acceptance.py --environment disposable-test --probe-network
# create a NEW private local folder; choose a fresh name, outside Git
python scripts/provider-fixtures.py --output-dir /tmp/opendev-acceptance-fixtures-new
```

Dry-run cannot be combined with network/execute flags. Invalid/missing environment selection fails closed. To perform the **read-only** live check later, the owner must first attest that the named project/bucket/app are disposable and dedicated, inject only acceptance-prefixed credentials through a protected mechanism, and explicitly select:

```sh
# Future owner operation only; not executed with credentials in this step
python scripts/provider-acceptance.py --environment disposable-test \
  --execute-read-only --confirm-disposable
```

`ACCEPTANCE_ENVIRONMENT=disposable-test` must also be present. Authenticated incomplete setup/failed checks exit 2. Dry-run and public network reports may exit 0 with missing/unavailable results; neither exit code nor a probe is a release approval. Client/proxy initialization failures also exit 2 with only a fixed redacted reason. A JSON `passed` scope is limited to Sandbox OAuth or exact private bucket metadata. Authenticated checks require dedicated acceptance fields; application secrets are never substituted. Responses are raw-byte bounded to 16 KiB, redirects disabled, TLS verification/proxy trust preserved, no retries, 5-second network timeouts and a shared 20-second checked request budget. Only one request per selected check is attempted. Compressed responses are not requested/expanded. Errors contain fixed reasons, not headers, URLs, bodies or token values. Injected MockTransport results are explicitly labeled `mocked`, never live evidence.

The test ref must match lowercase alphanumeric format; Supabase URL is derived as one HTTPS `<ref>.supabase.co` host. Bucket must begin `opendev-acceptance-`. These guards reduce mistakes but cannot independently prove ownership/disposability: operator attestation/project inventory remains necessary. No bucket creation, RLS changes, object uploads/deletion or payment operations exist in this harness. Thus failed readiness has no provider object/transaction cleanup side effect.

For manual object tests: choose a fresh run UUID/prefix in the approved disposable bucket; record only generated synthetic fixture names/hashes and protected run-owned keys; disable upserts. Compare against that manifest before deleting anything. Do not delete objects whose create outcome is ambiguous until ownership/reconciliation is established, and do not delete someone else's object after a collision. After expiry testing, delete only run-created fixtures, confirm removal, reconcile any failed cleanup and remove only the private local directory this run created. Do not delete production buckets, existing receipts, unrelated keys or entire storage prefixes shared with other runs.

Local regressions, using **fresh migrated localhost `opendev_test_*` DBs only**, from `backend/`:

```sh
python -m alembic upgrade head
python -m alembic check
python -m pytest -q
python -m pytest -q tests/test_provider_acceptance.py
```

Set DATABASE_URL and TEST_DATABASE_URL to the same disposable local target first. Never substitute Neon. Frontend commands are npm test, both TypeScript checks, lint, default build, separate `ANALYTICS_STUDIO_EVALUATION=true` local output. Run PostgreSQL-backed Chromium variants sequentially using PHASE6_BROWSER_JOURNEY=1 (and TEST_STUDIO=1 only for isolated evaluation). Docker smoke uses only synthetic provider values and does not contact them. Final local image is `sha256:33abeb761a7c3b0b1d02aad96a11aae617bac54004aa0cdb93dfcb420eb5b1e2`; its bounded no-network/read-only smoke recorded startup 6.69 seconds, diagnostic processing 2.09 seconds, child CPU 1.91 seconds, maximum individual child RSS 62,596 KiB, container peak 176,332,800 bytes and post-run 68.95 MiB/512 MiB. These are synthetic local measurements, not live-service, hostile-load or Render capacity proof.

## 7. Required credential/configuration names

| Scope | Names only | Source/handling |
| --- | --- | --- |
| Explicit selection | ACCEPTANCE_ENVIRONMENT | Must equal disposable-test for authenticated checks |
| Dedicated PayPal Sandbox | ACCEPTANCE_PAYPAL_CLIENT_ID, ACCEPTANCE_PAYPAL_CLIENT_SECRET, ACCEPTANCE_PAYPAL_WEBHOOK_ID, ACCEPTANCE_PAYPAL_MERCHANT_ID | Dedicated Sandbox developer app/business merchant; never production credentials |
| Dedicated Supabase | ACCEPTANCE_SUPABASE_PROJECT_REF, ACCEPTANCE_SUPABASE_STORAGE_BUCKET, ACCEPTANCE_SUPABASE_SERVICE_ROLE_KEY | Owner-verified disposable project and private acceptance-prefixed bucket |
| OAuth presence only | ACCEPTANCE_GITHUB_CLIENT_ID, ACCEPTANCE_GITHUB_CLIENT_SECRET, ACCEPTANCE_GITHUB_CALLBACK_URL | Optional test OAuth setup; no code exchange initiated by harness |
| Application presence only | PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET, PAYPAL_WEBHOOK_ID, PAYPAL_MERCHANT_ID; SUPABASE_URL, SUPABASE_STORAGE_BUCKET, SUPABASE_SERVICE_ROLE_KEY; GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET, GITHUB_CALLBACK_URL | Membership-only diagnostics; not used for live acceptance authentication |
| Application controls | CHECKOUT_ENABLED, RECEIPT_PROCESSING_ENABLED, LLM_ENABLED | Keep production false; explicit values only are reported, no changes made |

Never pass actual values as CLI arguments, commit an acceptance environment file or print process environment. No keys were generated, accessed from private credential files or rotated. No test credential is configured in this task's managed bindings or acceptance-prefixed environment.

## 8. Automated results versus real provider verification

| Final check | Actual result |
| --- | --- |
| Complete backend suite | **595 passed**, 0 failed/errors/skipped, 2 warnings, 332.96 seconds; 567 preceding +28 new cases |
| Complete frontend suite | **87 passed**, no failures/skips/cancellations |
| Both TypeScript configurations / lint | Pass; lint retains two existing AuthContext warnings |
| Community and separate local Studio evaluation builds | Pass; existing >500 kB chunk warnings remain; default output is Community |
| Fresh Alembic upgrade/check and financial preservation | Pass at unchanged b7a200000001; no migration source change |
| New focused provider/fixture cases | 27 passed, then concurrent capture/webhook case 1 passed; all 28 included in final full suite |
| Real local OCR fixture batch | 9 tested: 4 valid with total 1234, 5 expected rejections; temp directory cleaned |
| PostgreSQL-backed Community Chromium | 1 passed, 6 intentionally deselected, 13.36 seconds, existing deprecation warning |
| PostgreSQL-backed isolated Studio Chromium | 1 passed, 6 intentionally deselected, 26.25 seconds, existing deprecation warning; local trial only |
| Docker Community startup/static/disabled upload/OCR | Pass under bounded no-network/readonly profile; no provider authentication or transactions |
| Readiness dry-run | No dedicated test credentials; no auth/provider operations |
| Live external / genuine staging webhook | Not run/blocked, not a pass |
| Current source credential heuristic / whitespace | Zero candidate categories, zero historical blobs read; whitespace clean; no files staged |

Backend warnings remain Starlette's HTTPX TestClient deprecation and pypdf add_js deprecation in a synthetic hostile-file fixture. No warnings or deselected checks are disguised as successful live acceptance. Standalone optional Studio omitted-peer diagnostics and public licensing remain as documented in Step 3. No new package/dependency/lockfile changes occurred.

A manually injected malformed proxy environment did not exercise the expected initialization failure under the managed runtime; a deterministic MockClient exception then verified redacted exit 2 with no network. That is mocked failure-path evidence, not a live-provider result. Earlier 588-case run passed before six fixture/probe cases and one race case were added. The 27-case focused set and isolated race regression pass; the final full run includes all 28 new cases. Early focused invocations used the wrong working directory and collected no tests; corrected backend-directory invocations pass. This is a command setup error, not a live-provider failure.

**Live status:** PayPal OAuth/order/approval/capture/refund/signature verification not run; genuine webhook delivery blocked; Supabase authenticated metadata/object/RLS/signing/expiry checks not run. Dry-run artifacts are never live successes. Public HEAD returned `unavailable`, not successful authenticated access. No live GitHub OAuth, Ollama, hosting or production database acceptance is claimed.

## 9. Genuine webhook reachability

No verified public staging endpoint exists in this workspace, and none was exposed. **Real delivery remains blocked.** Options requiring separate owner approval: a temporary free native HTTPS test host; a restricted staging app with dedicated disposable DB/Sandbox configuration; or an approved temporary HTTPS forwarder that exposes only the webhook route. No host/tunnel was started, no hostname assigned and no free-tier capacity assumption made.

Stage controls must keep public UI/write routes restricted, receipt processing/LLM off and checkout off until an authorized test window with test-user access and actual acceptance approval. Preserve `/api/paypal/webhook` signature verification/body size bound and server-side authoritative order/capture/merchant checks. A webhook must not require browser OAuth/CSRF or a shared-secret query string; do not disable provider signatures to bypass staging access controls. Register the exact HTTPS path and returned Sandbox webhook ID with the matching Sandbox app. Verify TLS, edge forwarding, sanitized logs and provider receipt/retry records.

PayPal simulator events can test transport only; local generated JSON can test rejection/replay only. Genuine transaction delivery requires an actual authorized Sandbox transaction, provider transmission headers, verification SUCCESS, matching app/capture attribution and committed local state. Preserve raw sensitive evidence only in an owner-approved private record, with masked references in the public report. Duplicate delivery must have one financial effect. Modified signatures/body must be rejected without an event claim. Current repository tests deliberately mock verification and do not establish that real delivery occurred.

## 10. Security audit and confirmed fixes

Confirmed availability/error-handling defects: malformed approval ports/brackets could raise raw ValueError outside the intended sanitized HTTP error path; malformed signed refund parent URLs could similarly escape. Approval handling now validates link containers/entries and rejects bad URLs as generic 502. Refund parsing rejects malformed URLs as generic 400 and rolls back the claimed event; user-info, nonstandard ports, query and fragment references are rejected before capture-ID extraction. No arbitrary links are followed. Added regressions confirm no sentinel/token value in responses and no persisted bad-event claim. This is not a claim that an SSRF/money-theft exploit was found: authoritative requests already use fixed Sandbox endpoints and financial attribution checks remain unchanged.

Other reviewed controls: signatures before event claims, durable event/refund idempotency, row locks, immutable observation/sum constraints, bounded streamed webhook size (256 KiB), provider timeouts, backend-only service-role keys, private bucket requirement, 60-second URLs, project authorization, generated no-upsert object keys, cleanup reconciliation, no-store/no-referrer/nosniff and strict production feature defaults. General ingress quotas, provider callback load and host resources remain unverified; do not equate body/process limits with an OS sandbox. No security setting or license gate was weakened.

## 11. Credential rotation verification

**Owner verification required**, unchanged. Historical database/GitHub OAuth revocation/incident scope is not proven by deletion, a clean current tree or a disposable test credential. Owner must revoke/rotate genuine exposed values, review provider/DB/CI/artifact/fork access and supply sanitized provider-side completion evidence. Do not test leaked credentials or copy values into reports. Existing exposure references are in the redacted Step 1 artifact; no historical secret blobs were re-extracted here.

## 12. Exact remaining owner actions

1. Confirm original credential revocation/incident scope, application licensing/notices and current free infrastructure constraints.
2. Provision/identify distinct disposable Sandbox Business merchant/Personal buyer, Sandbox app/webhook registration and disposable Supabase project/private bucket. Do not supply production keys or personal receipts.
3. Inject the named dedicated acceptance variables securely, attest disposability, run dry-run/read-only checks and retain redacted scope-limited results. A green OAuth/private-metadata check does not close the other matrix rows.
4. Obtain separate approval for a restricted reachable staging webhook path and any test financial actions. No staging deployment or automatic refund is authorized by this report. Keep unsafe public feature gates closed.
5. Perform authorized manual checkout/approval/capture and genuine callback tests; separately authorize each Sandbox refund/reversal procedure. Reconcile exact records/entitlements and historical unknown coverage, including limited-tier uncertainty.
6. Run disposable object ownership/RLS/public-denial/signing/real-expiry/failure/redaction checks with synthetic files; safely clean only this run's owned objects and record cleanup failures.
7. Verify actual OCR containment/quotas and target-host capacity, HTTPS OAuth/proxy/logging, restore, private model rights/connectivity if enabled, native spreadsheet/beta/mobile acceptance and hosted CI. Review evidence before any explicit promotion, commit/push or public deployment approval.

## 13. Next-step prerequisites

Continue isolated remediation only with this working tree and explicit separation of evidence classes. Before a live read-only acceptance operation, require protected disposable configuration, owner attestation and reachable provider egress. Before transaction/refund tests or a staging endpoint, obtain specific approval and defined test-account/run ownership, bounded amounts, isolation/access controls and cleanup/reconciliation plans. Public promotion additionally requires all public release gates closed with actual evidence, not just a feature flag or local test count. Optional Studio remains isolated/local without public entitlement.

## 14. GO / NO-GO

**NO-GO for public deployment.** GO for local synthetic testing and owner review of prepared acceptance steps. No real provider acceptance, genuine webhook delivery, rotation, host capacity or full decoder isolation is established. No automatic commit/push, public endpoint, production migration, paid service or provider-side transaction/refund/object mutation was performed.
