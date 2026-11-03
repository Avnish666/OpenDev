# Phase 7 Step 1: release freeze and blocker register

Step 6 demo/submission handoff (2026-11-04, Asia/Calcutta): see
[final handoff](phase7-final-handoff.md), [local demo](demo-setup.md) and the
[submission checklist](submission/submission-checklist.md). A guarded synthetic
fixture, normal-auth loopback launchers, actual public-page screenshots and final
acceptance evidence are prepared. This does not establish a completed video,
submission, sponsor eligibility, credential rotation, public licensing, genuine
provider acceptance, full document isolation or hosted capacity. **Public NO-GO
and all relevant open gates below remain.** Step 1 sections retain historical state;
the final handoff contains current repository and verification results.

Step 5 AI/capacity verification (2026-11-04, Asia/Calcutta): see
[AI and capacity verification](phase7-ai-capacity-verification.md). Backend 618,
frontend 87 and three relevant Chromium journeys pass locally. Deterministic
reference evaluations: 45/45; mocked model scenarios: 7/7. No local Ollama server
or weights are available; real inference and model resource measurements are
**NOT RUN**. The loopback-only explicit local-test benchmark is prepared without
downloads. P7-09 remains open, deterministic mode remains the public default
recommendation, and **NO-GO remains**. Local image measurements do not establish
Render Free capacity or close other release blockers.

Step 4 provider acceptance (2026-11-04, Asia/Calcutta): see
[live-provider verification](phase7-live-provider-verification.md). A dedicated,
dry-run-first harness and synthetic fixtures are prepared; no disposable provider
credentials or verified reachable staging webhook are available. Real PayPal,
Supabase and genuine webhook acceptance remain blocked/not run. Malformed PayPal
link handling is hardened and locally regression-tested. No feature gate was
enabled and **NO-GO remains**; local/mocked evidence does not close live gates.

Step 3 preflight (2026-11-04, Asia/Calcutta): production startup validation and
backend restricted-launch controls are locally verified (see current preflight for final regression
totals). See [the current preflight report](phase7-deployment-preflight.md) for the
manifest, measurements and manual checks. Credential rotation, hosted CI, true
decoder containment and actual free-host/provider acceptance remain unverified;
**NO-GO remains**. Disabled intake reduces exposed operations and does not close
these public release gates.

Assessment: 2026-11-03 UTC. **NO-GO for public deployment.** This is the
authoritative consolidated register for Phase 3–6 findings; those reports remain
historical evidence. Local tests and a local image do not authorize deployment.
No production credentials, production migrations, live payments, model downloads,
paid services, deployment, secret rotation, history rewrite, commit or push were used.

**Step 2 amendment (2026-11-03, Asia/Calcutta):** the register below now reflects
the permissive PDFium replacement, shared decoder/kernel controls and additive exact
refund observations. Sections 3–11 retain the **Step 1 snapshot** and its test totals;
the current implementation, final verification and migration head are documented in
[`phase7-deployment-preparation.md`](phase7-deployment-preparation.md). Credential
rotation, full containment and external acceptance remain unverified. NO-GO remains.

## 1. Repository state and preservation

Initial branch: `main`. Initial/local/remote HEAD:
`fb5d5fcb015dc8678c309b451f615f6f7b1c9bc8` (`Phase 6 Step 5 done`). A read-only
remote lookup confirmed the same revision during this review. Step 4 is at
`e5ce99e`; Step 5 code includes public analytics navigation and secure exports.
Step 6 is present in these **initially uncommitted** files:

| Initial status | File |
| --- | --- |
| Modified | `frontend/src/api/dashboardFilters.ts` |
| Modified | `frontend/tests/analytics.test.mjs` |
| Untracked | `backend/tests/test_analytics_release.py` |
| Untracked | `docs/phase6-performance.json` |
| Untracked | `docs/phase6-release-readiness.md` |
| Untracked | `frontend/tests/browser-analytics-journey.mjs` |

Nothing was staged. Initial `git diff --check` passed. These six files were
preserved, including year-zero date validation and the benchmark/browser bridge.
No migration revision was edited or added. Phase 7 adds review documentation,
placeholder-only examples/ignore rules, a redacted scanner, narrow parser resource
fixes/tests and a same-origin Community deployment artifact.

Recommended sequence, **only after explicit user approval**: review and commit the
six Step 6 files together, create a Phase 7 hardening branch from that commit,
review and commit only the Phase 7 paths, then merge/push through the approved
workflow. Recheck the index and scan every staged diff before each commit; use
explicit paths, not `git add .`. Do not amend old commits or rewrite history.
Ignored `.env`, dependency trees, local test databases, build output and scan logs
must stay out of the index. The current work remains uncommitted on `main`.

## 2. Unified blocker register

Severity reflects potential impact, not proof of exploitation. “Public” means the
complete current application remains blocked; an optional-feature gate cannot be
cleared by silently removing functionality. Owners are responsible areas, not
claims that a specific person accepted work. Closed items have limited local scope.

| ID | Severity | Component | Evidence | Impact | Corrective action | Owner | Verification | Status | Gate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| P7-01 | High; critical if valid privileged credentials remain active | Credentials | Redacted Git scan finds database URL and GitHub OAuth secret candidates in `backend/.env.example` | Possible database/account compromise | Revoke/rotate, investigate access, review CI/artifacts/forks; see §6 | Owner / security / DB administrator | Provider-side old-credential revocation record, replacement configuration and access review, no values in evidence | Open; working example sanitized only | Public |
| P7-02 | High | Licensing / distribution | Step 2 replaces PyMuPDF with tested pypdfium2 5.14.0; no root project LICENSE/authorized whole-app notice record | New runtime avoids MuPDF AGPL; application/prior-artifact rights still unresolved | Review contributor/application rights, bundled notices and earlier distribution obligations | Owner / contributors / legal review | Replacement tests/no-MuPDF image verified; owner distribution/notice approval still required | Runtime remediated; overall licensing open | Public |
| P7-03 | High | Untrusted documents | Decoder subprocesses share application UID/filesystem/network permissions; no global ingress/project quota | Decoder compromise, resource/storage exhaustion | OS containment, bounded ingress/storage, hostile-file/concurrency acceptance; §3 | Backend / infrastructure / security | Prove no app secrets/network access from worker; memory/CPU/temp/process kill and abuse-load tests | Open; two resource defects fixed | Public |
| P7-04 | High | Render / Neon / resource budgets | Local host has much more RAM than a free web service; target quotas and proxy behavior unverified | OOM, exhausted pools, cold-start/request failures | Verify current free plans, TLS/pool limits, target-host load/cancellation and restore rehearsal | Infrastructure / DB administrator | Recorded concurrency/RSS/CPU/DB saturation, recovery and budget results on approved target | Open | Public |
| P7-05 | High | OAuth / HTTPS topology / logs | Same-origin image passes local health/static tests; real HTTPS OAuth/proxy acceptance absent | Failed login, cookie loss, leaked callback codes in edge logs | Use §7 topology; validate exact callbacks, Secure cookies, CSRF/CORS, two-account permissions and log redaction | Backend / infrastructure / security | HTTPS browser/provider checklist and safe edge-log retention record | Open; artifact prepared | Public |
| P7-06 | High | PayPal Sandbox integration | Synthetic capture, signature, duplicate and refund tests; no real test-account acceptance | Unreconciled captures/rewards on provider failures | Authorized Sandbox buyer approval/cancel/capture, delayed/duplicate/refund/reversal and operator recovery exercise | Payments / owner | Reconciled provider transaction IDs and app states with sanitized evidence | Open | Public |
| P7-07 | High | Partial refunds / public finance | Step 2 adds immutable refund IDs/amounts, authoritative cumulative/full-refund observations and migration b7a200000001 | Exact observed amounts now supported; unknown history/live-provider completeness unresolved | Review historical coverage and actual Sandbox reconciliation; never guess missing partial amounts/IDs | Payments / accounting | Local multiple/duplicate/reordered/concurrent/full-refund and report-parity tests pass; live/historical evidence required | Code remediated; historical/live gate open | Public |
| P7-08 | High | Supabase / redaction | Private bucket/signing/cleanup mocked; true redaction and live expiry unverified | Disclosure of original receipts or retained sensitive data | Synthetic private bucket access, redaction/metadata inspection, expiry/revocation and cleanup exercise | Storage / security / maintainers | Direct unauthenticated denial, manager/public boundaries, no originals published, signed-link expiry record | Open | Public |
| P7-09 | High | Ollama / AI | Local deterministic/fake-model acceptance; no installed model/server or real inference evidence | AI unavailable or unsupported claims despite typed tools | Approve reachable free private endpoint, model rights/version/capability, semantic and adversarial acceptance | AI / infrastructure | Real tools, refusal/injection/citation accuracy, latency, cancellation and private-data tests | Open | Public AI / complete release |
| P7-10 | Medium | Limited reward tiers | Abandoned/denied/cancelled attempts conservatively retain reservations | Capacity can remain unavailable indefinitely | Reviewed durable reconciliation and recovery policy; never infer payment failure from local age | Payments / operations | Pending/unknown capture, delayed completion and expiry race with no oversell | Open | Limited-tier feature |
| P7-11 | High for unauthorized use | Optional Studio | Studio 3.0.0 and Enterprise dependencies declare Commercial terms; local trial watermark | Unauthorized public use | Keep Community default; obtain and review explicit public rights before any Studio publication | Owner / licensing | Reviewed terms/entitlement for intended use; default bundle absence verified independently | Open for Studio; Community isolation verified | Optional Studio only |
| P7-12 | Medium | Bryntum beta / large frontend | Community packages pinned 8.0.0-beta.1/MIT; large lazy chunks | Browser/device/long-session reliability and transfer risk | Beta acceptance policy, broader browser/accessibility/mobile/slow-network and retention tests | Frontend / QA | Recorded target-device/browser budgets and repeated navigation | Open release risk | Public roadmap / dashboard acceptance |
| P7-13 | Medium | CI / dependencies / supply chain | Local checks pass; hosted CI logs unavailable; base/apt tags float; no full Python/OS CVE scan | Unreviewed build/log exposure or known vulnerable components | Owner inspect historical CI/logs; pin reviewed release image digests, inventory notices and run Python/OS advisory review | Release engineering / security | Sanitized CI run/log review, source-to-image digest and advisory disposition | Open | Public |
| P7-14 | Medium | CSV downstream use | Parsed-cell neutralization and Chromium downloads tested, native spreadsheet/re-save behavior unverified | Downstream formula interpretation or incorrect imports | Synthetic Excel/LibreOffice/import-policy acceptance | Frontend / security / QA | Hostile-cell open/import/re-save with no formula execution or privacy leak | Open acceptance work | Public exports |
| P7-F01 | Medium | OCR stdout | Parent previously buffered PIPE output before size check | Avoidable parent memory growth | File-backed stdout, worker file limit, size-before-read, bounded read | Backend | Oversized output and timeout/process-group regressions | Fixed locally | Defect closed; P7-03 remains |
| P7-F02 | Medium | Validator admission | Every request could spawn a validator | Avoidable per-process validator concurrency | Nonblocking single validation slot, 429/Retry-After, finally release, private busy extraction code | Backend | Busy rejection and error-release regression; full document tests | Fixed locally | Defect closed; global abuse gate remains |
| P7-F03 | Medium | Deployment preparation | Backend-only image did not provide same-origin frontend serving | Cookie topology required extra unproven routing | Combined Community image, static mount after API routes | Backend / infrastructure | Local build, non-root root/API/DB routes, missing/traversal tests | Fixed artifact locally | P7-05 live gate remains |
| P7-F04 | Medium | Validator output / combined decoder pressure | Step 1 still buffered validator PIPE and allowed validation during OCR | Parent buffering and concurrent native memory pressure | File-backed 4 KiB validation output, shared decoder slot, kernel/core/descriptor/no-new-privileges limits | Backend / security | Step 2 document/kernel regressions and constrained image OCR pass | Fixed locally | P7-03 containment remains |
| P7-F05 | High | Late reversal/refund ordering | A refund could overwrite already reversed status | Incorrect retained funding and reward eligibility | Preserve reversal precedence and transactional immutable refund accounting | Payments | Step 2 reordered/refund/full-status/duplicate/concurrent tests and DB constraints pass | Fixed locally | P7-06/P7-07 live gates remain |
| P7-F06 | High | PDF/image dependency advisories | Version-specific PyPI metadata reports affected Pillow 12.2.0 and pypdf 6.12.0; aliases overlap | Known flaws in libraries processing untrusted receipts | Pin Pillow 13.0.0 and pypdf 6.21.4; revalidate actual OCR and full suite | Backend / release security | Final 32-package PyPI metadata has zero reported entries; rebuilt image/full regression evidence in Step 2 report | Dependency remediation locally verified; not an OS/native security clearance | P7-03/P7-13 remaining gates |

Accepted local limitations: retained/sampled GitHub data is not a complete audit;
delivery/fulfillment are maintainer assertions; current-owner history is not lifetime
authorship; receipts are not proof of payment; financial differences are not escrow
or bank balances; quotas are worker-local and cancellation is partly cooperative.
Existing labels/nulls/denominators stay visible. Public acceptance still needs the
register's relevant evidence rather than a claim of complete provenance.

## 3. Security findings and document hardening

Confirmed fixes (no extraction engine or payment rewrite):

- OCR JSON previously used `communicate()` with PIPE and checked 250,000 bytes only
  after buffering all output in the API parent. It now uses a private temporary
  regular file, making the worker's 8 MiB `RLIMIT_FSIZE` applicable to stdout, checks
  file size before reading, and reads at most 250,001 bytes. Timeout still kills
  and drains the whole extraction process group. Temporary output closes on every
  exit. This bounds ordinary worker output; a compromised worker is still P7-03.
- `documents.validate()` now admits one validator per process, rejects busy calls
  with 429/Retry-After 5, and releases on error. Extraction reports `VALIDATION_BUSY`
  privately rather than mislabeling overload as storage failure. This does not cap
  uploads that are still streaming, distributed instances, total disk or storage.

Existing controls inspected in `routers/documents.py`, `services/documents.py`,
`document_validation_worker.py`, and `services/receipt/{pipeline,provider,worker}.py`:

| Boundary | Actual bound / behavior | Remaining limit |
| --- | --- | --- |
| Upload | Authorize before body/storage; streamed 5 MiB maximum, 20-second deadline; private temporary filename, finally unlink | Concurrent uploads can consume aggregate disk/connections; no per-project storage quota |
| Signature / malformed input | PNG/JPEG signatures/trailers, Pillow verify+load, strict PDF header/EOF, encrypted PDFs rejected | Polyglots/native decoder vulnerabilities not excluded by signatures |
| PDF structure | 1–100 pages; bounded 50,000-object traversal; reject JavaScript, actions, launch/rich media, attachments, forms/XFA | Structure validation is not exploit containment or proof of visual redaction |
| Validation process | Python `-I`, empty environment; 256 MiB address space, 5 CPU seconds, zero file-write limit; 8-second parent timeout; one admitted worker/process | Same UID/OS permissions; ordinary worker stdout is tiny but validation PIPE is not an independent malicious-worker containment boundary |
| Extraction | 320 MiB address space, 50 CPU seconds, 8 MiB file limit; 60-second parent timeout kills process group; bounded schema/result | Limits are per process, not total native child/API RSS or a container-wide security sandbox |
| Page/image expansion | Extraction at most 5 pages; 20-million-pixel image check, PDF raster longest side 2,000 pixels/zoom ≤2; image thumbnails bounded | Large intermediate decode/stream expansion can fail within worker limits; reject rather than promise all files work |
| OCR | Tesseract 12 seconds/page; minimal environment/one OpenMP thread; TSV ≤2 MiB, line/text/result bounds | English only; hostile/native failures and simultaneous pipeline/validation still require resource acceptance |
| Pipeline | Private work directory, downloaded size/hash/MIME recheck; DB advisory lock serializes extractor, lease recovery | Lock is throughput control, not isolation; temp retention/lease/operator recovery needs host tests |

The Docker user is non-root, but parser and API share UID, filesystem and network
permissions. An empty child environment does not prevent reading application files,
parent process data or making network connections after a decoder compromise.
No confirmed code-execution exploit was established; **complete isolation was not**.

Free mitigation plan: keep one web worker; add bounded request admission before
streaming and per-owner/project storage quotas with cleanup/retention; limit reverse
proxy request duration/size/rate; move decoder execution behind an OS-enforced
boundary with read-only input, bounded writable tmpfs, no network, no secrets,
separate UID/process visibility, dropped capabilities/no-new-privileges and cgroup
RAM/CPU/process caps. A container configuration option alone does not isolate a
child from its parent. Check whether the actual free host supports the boundary;
otherwise evaluate a free owner-controlled isolated runner while retaining the
monolith's service interface. Do not expose a Docker socket to the web application.
Validate hostile fixtures and combined load before selecting quotas. No functionality
was removed and no isolation-complete claim is made.

## 4. Licensing and sponsor package assessment

Installed runtime/test dependency metadata and both npm locks were inspected.
The runtime/test closure has **32 Python distributions**; the main frontend lock
has **92 non-root package entries**. This excludes legacy scientific/notebook
`requirements.txt` from the web image; it is not an OS SBOM or legal opinion.

- AG Grid Community 36.2.0 and AG Charts Community 14.2.0 declare MIT. The main
  package/lock contain no Studio/Enterprise packages. Default build alias selects
  `StudioUnavailable`; the combined image excludes `frontend/studio` entirely.
- AG Studio/ag-studio-react 3.0.0 declare Commercial terms, with required isolated
  Grid Enterprise 36.2.0 and Charts Enterprise 14.2.0. Installed vendor material
  advertises a 45-day trial; missing-key banners/watermarks in local evaluation
  confer no unrestricted public rights. No key was generated or supplied. Runtime
  flags and a license-key string are not legal authorization. Preserve the user's
  restriction: Enterprise dependencies only in the optional installation.
- All nine Bryntum Community lock entries are MIT-declared 8.0.0-beta.1. Preserve
  notices and explicitly accept beta limitations; Community rights do not extend
  to vendor commercial products. Browser/long-session risks remain P7-12.
- APIMatic PayPal Context Plugin 0.4.1 was development assistance documented in
  `docs/paypal-context-setup.md`; it is not a shipped PayPal runtime dependency.
  The payment adapter uses HTTPX and the fixed PayPal Sandbox API. No paid API or
  new SDK was introduced. Recheck plugin terms before redistributing its material.
- FastAPI/React/Vite and most runtime components use permissive notices;
  SQLAlchemy/Alembic MIT, HTTPX BSD, Pillow MIT-CMU, pypdf BSD, psycopg LGPL and
  Tesseract Apache obligations still need bundled notices/dependency review.
  Inventory license strings do not prove source/distribution compliance.

References: [AG Studio licensing](https://www.ag-grid.com/license-pricing/),
[Studio npm metadata](https://www.npmjs.com/package/ag-studio/v/3.0.0),
installed package LICENSE/README and both lockfiles;
[Bryntum Community](https://bryntum.com/products/gantt/community/).
Vendor terms/current public deployment rights were not independently established.
Do not publish the evaluation bundle. The default Community path is independent
of P7-11, but other public blockers remain.

## 5. PyMuPDF decision and alternatives

**Retain PyMuPDF 1.26.7 unchanged; keep P7-02 open.** It supplies PDF text/word
bounding boxes and raster pages for scanned receipt OCR in `receipt/worker.py`.
Removing its import without equivalent rendering/layout behavior loses evidence
extraction functionality. pypdf already validates structure, not rendered OCR.

Installed and version-specific PyPI metadata both declare “Dual Licensed - GNU
AFFERO GPL 3.0 or Artifex Commercial License.” The free route requires an authorized
assessment of the application/MuPDF relationship, contributor rights and compatible
dependency terms, required notices and complete corresponding source (including
build/install material), and an appropriate source offer to remote users where
AGPL §13 applies. Merely having a public repository does not settle those duties.
No root application LICENSE or approved compliance/distribution plan exists here;
we cannot unilaterally license contributors' code. No commercial purchase is proposed.

| Free option | Declared license evidence | Features / OCR suitability | Tradeoff / decision |
| --- | --- | --- | --- |
| Existing PyMuPDF 1.26.7 | AGPL-3.0 or commercial, version-specific metadata | Text/word boxes and raster, current Tesseract adapter | Fast/native but current isolation bounds still apply; free AGPL route needs authorized legal/compliance review |
| pypdf 6.12.0 (installed) | BSD-3-Clause | Structure and text; no PDF rasterizer | Cannot alone replace scanned-page OCR; untrusted stream expansion still needs limits |
| pdfminer.six 20260107 (candidate metadata) | MIT | Text/layout extraction; no rasterizer | Pure Python is not an exhaustion sandbox; separate rendering engine required |
| pypdfium2 5.14.0 (candidate metadata) | BSD-3-Clause / Apache-2.0 plus dependency licenses | Native PDFium rendering/text/bounding information, potentially feed Tesseract | Most plausible permissive replacement spike; verify bundled PDFium/component notices, bbox/rotation/text quality and native resource behavior |
| Pillow 12.2.0 (installed) | MIT-CMU | PNG/JPEG decode; current image OCR | Does not replace PDF text/raster functionality |

Public metadata was fetched on assessment date, without installing alternatives:
[PyMuPDF 1.26.7](https://pypi.org/pypi/PyMuPDF/1.26.7/json),
[pypdf 6.12.0](https://pypi.org/pypi/pypdf/6.12.0/json),
[Pillow 12.2.0](https://pypi.org/pypi/Pillow/12.2.0/json),
[pypdfium2](https://pypi.org/pypi/pypdfium2/json),
[pdfminer.six](https://pypi.org/pypi/pdfminer.six/json).
Legal sources requiring owner review:
[GNU AGPL text, especially §§1, 5, 6, 13](https://www.gnu.org/licenses/agpl-3.0.html),
[Artifex licensing](https://artifex.com/licensing/),
[pypdfium2 licensing](https://github.com/pypdfium2-team/pypdfium2#licensing).
Live vendor legal pages were not independently verified; metadata is not a legal
interpretation. No alternative was installed, benchmarked or silently substituted.

Next free-path decision: owner/legal review chooses either a documented compatible
AGPL distribution/source-offer plan or authorizes a separately scoped pypdfium2
spike. A replacement needs text/scanned/rotated/malformed/encrypted/multi-page cases,
word-box/schema parity, extraction-version change, OCR accuracy and low-memory
timeouts/process cleanup, plus removal of unused MuPDF dependencies and notices.

## 6. Credential exposure review and rotation

See value-free [`phase7-credential-review.json`](phase7-credential-review.json) and
`scripts/release-credential-audit.py`. The local non-shallow repository scan covers
  27 reachable commits, 391 unique blob/path pairs, zero blobs over the 1 MiB cutoff,
  and 269 non-ignored source/configuration files at the final scan. UTF-16 history is handled. Private
working `.env`/key files and symlinks are deliberately excluded. The heuristic
collects matches internally but emits only paths, categories and identifiers;
it never authenticates, calls a provider or prints a credential value.

| Path | Representative containing commit | Category | Disposition |
| --- | --- | --- | --- |
| `backend/.env.example` | `fb5d5fcb015dc8678c309b451f615f6f7b1c9bc8` | Database password URL; GitHub OAuth Client Secret | Potential exposure; treat as compromised if genuine until owner proves revocation |
| `backend/.env.example` | `8d634d2ada3a00b484ecbde82886d61bc9c0799e` | Database password URL | Historical exposure candidate; same required review |

These are containing commits, not a claim to identify first exposure. Working
examples now use placeholders and the current-source scan finds no candidates.
Deleting/replacing an example **does not revoke** the committed/history values.
No live validity or exploitation was tested. The heuristic found no additional
PayPal Client Secret, Supabase service-role, Studio key or session-secret candidates;
that does not prove none exist in unscanned repositories, forks, artifacts or logs.
Sessions use random tokens stored as hashes, not a shared signing-secret setting.

Reviewed the CI workflow (synthetic local Postgres values, no backend secrets in
frontend jobs), examples/docs, client build variable boundaries and image context.
Read-only GitHub Actions metadata access failed; **live CI logs/artifacts were not
inspected**. Raw errors/log output was withheld. Owner review remains mandatory.
Default image contains zero `.env`/private-key/Git/dependency-directory artifacts
under `/app` by filename check and no Studio SDK asset filenames. Client builds
were heuristically checked for backend-secret/database markers, not compared with
real secret values. This is not a complete historical incident investigation.

Manual instructions, highest priority, executed by authorized owners outside this
task (never paste replacements into chat/Git):

1. Identify the affected database role/provider and GitHub OAuth application in
   their dashboards. Revoke/rotate any genuine exposed database password and OAuth
   client secret immediately; remove old OAuth secrets rather than just adding a
   second active one. Review DB roles, access logs, unexpected sessions/queries,
   OAuth activity and the likely exposure window; preserve sanitized incident facts.
2. Generate least-privilege replacements in the provider UIs and update backend
   host secret settings only. Recycle affected application connections and verify
   with an approved synthetic acceptance flow. Invalidate affected application
   sessions if incident scope warrants it. Record revocation timestamp/reference,
   responsible owner and verification result without values.
3. Review hosted CI history/artifacts, build logs, releases, forks and shared copies
   for the listed credential categories. If further genuine exposure is found,
   revoke the PayPal Sandbox secret in its developer app, Supabase service-role
   credential through its supported key-rotation procedure (coordinate dependent
   services), and Studio entitlement through its vendor as applicable. Do not
   assume rotating an unrelated key revokes legacy JWT/service-role credentials.
4. Confirm old credentials are disabled using provider-side evidence in a separate
   authorized incident workflow, not by testing leaked values from this checkout.
   Document redacted completion evidence. Consider coordinated history cleanup
   only after revocation and explicit approval; rewriting Git cannot recall forks.

## 7. Authentication and deployment topology

Prepared [`deploy/Dockerfile`](../deploy/Dockerfile), root `.dockerignore` and
[`deploy/README.md`](../deploy/README.md). One HTTPS native Render hostname routes
both React/hash routes and `/api` to a single FastAPI process. The frontend build
uses empty `VITE_API_URL`, relative API requests and Community renderer. The static
mount is last, preserves registered API routes and rejects missing/traversal paths;
it is off by default in development/tests unless `FRONTEND_DIST` is set.

Use `APP_ENV=production`, exact `FRONTEND_URL=https://<native-host>` with no trailing
slash, and matching GitHub callback `https://<native-host>/api/auth/github/callback`.
No paid custom domain is required. Separate unrelated static/API origins are not
an accepted topology for current SameSite=Lax authenticated fetches. Do not loosen
cookies, Origin checks or CORS to bypass deployment failures.

Source review: OAuth state uses a random HttpOnly, Lax, 600-second cookie restricted
to `/api/auth/github`; production makes it Secure. Session tokens are random,
SHA-256 hashed in DB, expire after seven days, and are revoked on logout; production
session cookies are Secure/HttpOnly/Lax. Mutating browser endpoints require the exact
trusted Origin in addition to server-side authorization. CORS allows that origin
with credentials; wildcard allowed headers are not wildcard origins. Public data
selectors mask drafts, private evidence/backer identities and cross-project access.
The PayPal webhook is the intentional non-browser write boundary: fixed Sandbox
verification API and configured webhook ID, signature verification and durable event
deduplication, not browser Origin. API responses, including errors, set no-store,
no-referrer and nosniff. Provider errors are sanitized; image disables Uvicorn access
logs to reduce callback-code leakage. Edge/proxy logs remain unverified.

Local HTTP tests do not establish HTTPS login, registered OAuth settings, Secure
cookie persistence, CORS preflights, cross-account cache behavior or edge redirects.
P7-05 requires actual approved HTTPS acceptance and log redaction. Do not treat
the liveness endpoint as readiness for every external dependency.

## 8. Payment reconciliation and rewards

Keep PayPal Sandbox and existing deterministic logic. Server derives amounts and
currency from stored tiers; checkout/capture request keys and locks prevent duplicate
financial effects; webhook event IDs are persisted once and verified against the
Sandbox API. Reward entitlements are tied to completed contribution state and
revoked for refund/reversal states; fulfillment/authorization tests remain in the
full regression suite. No money movement or payment code rewrite was performed.

Existing contribution/capture state and webhook metadata do not retain exact
refund transaction amounts/IDs. Accurate historical partial-refund arithmetic
cannot be reconstructed safely from those records alone. No invented prorating,
OCR-derived amount or unsafe backfill was added. Reports conservatively exclude
the original capture amount in full when refund/reversal-affected; exact refunds
remain unknown/null. Existing public financial/transparency/analytics/export and
AI disclosures explain the limitation; it is not a verified cash balance. P7-07
remains a deployment gate even with that disclosure.

Abandoned limited-tier reservations remain conservative to avoid overselling; do
not release capacity based only on local time or a failed client request. Delayed
capture can still arrive. A future reviewed operator/provider reconciliation path
must handle uncertain status, duplicates, webhook order, pending captures and
reward fulfillment history. P7-06 acceptance includes real signed Sandbox events,
full/partial refunds, reversals and ambiguous-outcome recovery. Unlimited tiers can
support isolated testing but do not close the limited-tier feature gate.

## 9. Free-tier infrastructure requirements

The combined image builds with Node 24 and Python 3.12 Bookworm, installs Tesseract
plus English data and CA trust, pinned web requirements only, serves built static
assets and runs UID 10001 / one Uvicorn worker. It accepts `PORT` (default 10000),
has `/api/health` Docker liveness, and does not migrate DB, initialize storage or
download models at startup. Existing backend-only Dockerfile remains available.
The BuildKit proxy CA mount is public trust material, not runtime credentials.

| Resource | Required before release |
| --- | --- |
| Render Free | Verify current availability/quotas/idle shutdown, request duration, health behavior, native HTTPS and operational terms. Local idle RSS is not capacity proof; exercise concurrent parser/OCR/API/exports, cold starts and recovery. Check unsupported isolation features explicitly. |
| Neon PostgreSQL | Verify current free storage/compute/connection limits, region/latency, TLS, backup/restore and cold wakeups. SQLAlchemy pool size 3 + overflow 2 is per engine/process, not a global connection budget; budget workers, migrations, operators and background connections together. Rehearse migration outside startup. |
| Supabase | Private bucket, backend-only service-role key, approved redaction, signed URLs 60 seconds, direct access denial, quotas/cleanup and residual signed-link validity until expiry. Private originals never become public automatically. |
| Frontend | Same-origin static artifact avoids extra paid domain/proxy. Large Community/Studio chunks still require mobile/slow-network budgets; optional Studio is excluded from the public candidate. |
| Ollama | No daemon/weights in image. An owner-controlled free host must be securely reachable; Render localhost cannot reach a laptop. Validate model terms, tool calling, context/RAM and adversarial answers. `trust_env=False`/no redirects is not endpoint availability or external authentication. Do not expose an unauthenticated model endpoint publicly. |
| Operations | Ingress/request/storage budgets, alerts/manual reconciliation, private log retention, crash/temp cleanup, database restore and approved rollback plan. Ephemeral web disk is temporary processing space, not durable receipt storage. |

The local image measured about 68.6 MiB idle RSS via Docker stats on a 33.3 GiB
host; this is a single observation, not peak native memory, OCR load, GPU/model RAM
or Render Free suitability. Validation and extraction limits alone can consume a
large portion of a small host, plus API, Tesseract children and DB client memory.
Phase 6 benchmark JSON remains the reference for synthetic SQL/query/response-size
measurements; it does not establish host throughput. No production service was
created or queried in this step.

## 10. Tests and verification results

| Check | Actual result |
| --- | --- |
| Full backend suite, fresh migrated local PostgreSQL 16 | **519 passed**, 0 failed/errors/skipped, one Starlette HTTPX deprecation warning; 282.63 seconds |
| Full frontend suite | **86 passed**, 0 failed/skipped/cancelled |
| Main TypeScript and isolated Studio TypeScript | Both pass (`tsc -b`, `tsc -p studio/tsconfig.json --noEmit`) |
| Community build and isolated local Studio evaluation build | Both pass; Vite warns about chunks larger than 500 kB. Final default `dist` is Community; Studio output goes to `/tmp/opendev-phase7-studio-build` |
| Lint | Exit 0, two existing AuthContext warnings: component-only exports and set-state-in-effect |
| Alembic fresh upgrade/check/current | Pass, no schema drift; sole head `8c6072dabc59`; no migration source changed |
| Main dependency tree / Python `pip check` / image `pip check` | Pass; optional standalone tree exception documented in §11 |
| npm audits, main and optional Studio locks | Both report 0 known vulnerabilities, no audit errors at assessment time |
| License inventory | 32 Python distributions, 92 main frontend lock entries; nine MIT-declared Bryntum beta entries; optional Commercial entries independently confirmed |
| Community and Studio mock-API Chromium smoke journeys | Both pass when run sequentially; real charts/grid, filters/presets, malicious text, errors, CSV, mobile and navigation cleanup |
| PostgreSQL-backed Community Chromium journey | **1 passed**, 6 intentionally deselected, one deprecation warning; 7.56 seconds |
| PostgreSQL-backed local Studio Chromium journey | **1 passed**, 6 intentionally deselected, one deprecation warning; 14.47 seconds; vendor trial/no-key banners expected |
| Combined Docker build and local runtime smoke | Pass; details §11; no public host or production credentials |
| Credential heuristic / Git whitespace/index | Historical candidates remain; working-source candidates 0; whitespace passes and index remains empty |

Initial unsuccessful invocations are not hidden: the first full backend attempt
omitted the public-schema migration and returned 391 passes / 128 fixture setup
errors (`users` table missing), rather than a product regression. The complete
rerun migrated a new isolated PostgreSQL instance first and passed all 519. The
local test-only instance uses 256 MiB shared memory; the pre-existing container
and data were preserved. A first Studio smoke run concurrently with Community
failed dynamic module loading; a sequential rerun passed, consistent with shared
Vite optimizer cache interference. An initial TypeScript command referenced a
nonexistent `tsconfig.studio.json`; the actual `studio/tsconfig.json` passes.
No skipped, deselected, failed or unavailable check is represented as a pass.

Reproduction, on a **fresh migrated local `opendev_test_*` database only**:

```sh
# backend/; set both DATABASE_URL and TEST_DATABASE_URL to the same disposable DB
APP_ENV=testing alembic upgrade head
APP_ENV=testing alembic check
APP_ENV=testing python -m pytest -q
PHASE6_BROWSER_JOURNEY=1 APP_ENV=testing python -m pytest -q -s tests/test_analytics_release.py -k real_public
TEST_STUDIO=1 PHASE6_BROWSER_JOURNEY=1 APP_ENV=testing python -m pytest -q -s tests/test_analytics_release.py -k real_public

# frontend/; optional Studio installed separately with npm --prefix studio ci --omit=peer
npm test
npx tsc -b
npx tsc -p studio/tsconfig.json --noEmit
npm run lint
npm run build
ANALYTICS_STUDIO_EVALUATION=true npm run build -- --outDir /tmp/opendev-phase7-studio-build
node tests/browser-analytics-smoke.mjs
TEST_STUDIO=1 node tests/browser-analytics-smoke.mjs
```

Run Vite browser variants **sequentially**: both use the same dependency optimizer
cache. Optional evaluation output must remain local. Run `pip check`, main/optional
`npm audit --json`, main `npm ls --all`, the license inventory and value-free credential
scanner. Bare optional-install `npm ls` reports omitted React peers; the application
supplies React/ReactDOM from its parent and Vite deduplicates them (see §11).

## 11. Resolution evidence and limits

- `backend/tests/test_phase7_hardening.py` adds four regressions: OCR file-backed
  output bound, timeout group kill/drain, validation busy/error release, and
  same-origin static/API precedence/missing asset/traversal/configuration handling.
  Existing extraction/document/security suites exercise actual local decoders.
- Combined image built locally as `opendev-review:phase7`. Loopback-only container
  returned 200 HTML at `/`, 200 JSON/no-store at `/api/health` and `/api/db-health`,
  and 404 for unknown API/assets. UID is 10001; OCR lists `eng` and `osd`; image
  `pip check` passes. Artifact filename checks found no credential/history paths
  under `/app` and no Studio SDK-named asset. No startup migration occurred.
  Final reviewed image ID is
  `sha256:8f78f00b640cd06c078a877dacedc17a8161e1d2351212ce9f9256b5333d7881`.
  The refreshed image also returned a no-store 401 for anonymous profile access,
  set production OAuth state Secure/HttpOnly/Lax with a 600-second lifetime and
  the restricted path, allowed only the configured CORS origin, and rejected an
  untrusted-origin logout with 403. Redirects were not followed and no provider
  was contacted. This is local flag/configuration evidence, not live HTTPS OAuth.
- After a stronger existing-file traversal assertion, all four targeted hardening
  regressions passed again (0.71 seconds, one existing deprecation warning). The
  final Community bundle has six JS assets, no SDK Studio renderer and none of the
  checked backend-secret variable/database URL markers. Studio output remains in
  the separate local `/tmp` directory. Neither scan compares actual secret values.
- Root/main examples and Docker ignore rules prevent ordinary future secret-file
  inclusion; they cannot sanitize Git history, a malicious source literal, an
  arbitrary file named outside the denylist or credentials passed at runtime.
- Optional Studio intentionally omits peer copies (`npm --prefix studio ci --omit=peer`).
  `npm ls --all` in that isolated directory exits 1 for missing local React/ReactDOM
  peers, also with `--omit=peer`; this is reported rather than hidden. Node resolution
  from `ag-studio-react` resolves both to the exact same parent copies as the app;
  Studio types/build and isolated browser acceptance pass. No duplicate peer install
  was added merely to silence this standalone tree diagnostic.
- No production/provider service acceptance, hosted CI log review, actual credential
  revocation, Python/OS vulnerability scan or legal compliance signoff is claimed.
  npm advisory results are time-specific and cannot establish zero vulnerabilities.

## 12. Remaining manual actions, in priority order

1. Owner/security: contain P7-01, rotate/revoke genuine database/OAuth exposures,
   investigate logs and obtain redacted evidence. Inspect hosted CI logs/artifacts.
2. Owner/legal/contributors: decide P7-02 free license path and establish application
   rights, corresponding source/notices/source offer, or authorize replacement work.
3. Backend/infrastructure: resolve P7-03 OS containment and global ingress/storage
   budgets, then validate target free-host capability/capacity and DB restore.
4. Payments/accounting: separately design authoritative refund ledger and reconcile
   limited-tier reservations; perform authorized real Sandbox recovery exercises.
5. Infrastructure/security: provision only after separate approval, then verify
   same-origin HTTPS OAuth, private Supabase and secure model connectivity using
   synthetic data/test accounts. Validate logs/cache/proxy and two-account isolation.
6. QA/release: native spreadsheets, broader/browser/mobile/beta acceptance, CI and
   dependency advisory/distribution notices, immutable artifact review. Keep Studio
   disabled in public artifacts unless explicit licensing evidence is obtained.
7. Ask for explicit approval of a concrete reviewed commit/branch sequence; do not
   stage, commit, push, deploy or migrate production as part of this step.

## 13. Exact prerequisites for Phase 7 Step 2

For **continued isolated remediation/testing**, preserve this working tree, review
the final checks, assign owners and evidence to every open register item, agree
which blockers Step 2 will address, and obtain approval before any commit/branch
mutation. That does not require or authorize a public release.

If Step 2 includes any hosted integration/deployment: first obtain explicit scope
and deployment approval; approved credential replacement/incident evidence; the
authorized licensing path; an approved untrusted-file containment/abuse plan; a
current zero-budget infrastructure/resource/restore plan; and a concrete reviewed
artifact, runtime-variable/callback plan and target database identity. Obtain separate
approval before target migrations. Public traffic additionally requires **all Public
gates** closed with attached verification, including live Sandbox/private-storage/
HTTPS/model acceptance and accurate refund-ledger resolution. Optional gates must
be closed before enabling their feature; lack of rights never authorizes Studio.

## 14. GO / NO-GO recommendation

**NO-GO for public deployment. GO for isolated review/remediation only.** Resource
fixes, safe examples and a tested same-origin build are concrete progress, but
cannot establish credential revocation, legal compliance, exploit isolation or
free-host/provider correctness. No inherited blocker is closed by test count alone.
No commit, push, deployment or production migration was performed.
