# Testing and limitations

Evidence describes local synthetic execution. External provider mocks, local browser
rendering and actual live-provider acceptance are different classes. This is a release
review, not a security/legal certification. The final handoff records the final suite
result after environment recovery; the Step 5 baseline was 618 backend / 87 frontend.

## Final Step 6 results

| Final check | Actual result |
| --- | --- |
| Complete backend suite, fresh migrated regression DB | **630 passed, 0 failed/skipped/errors**, 2 existing warnings, **334.99 s** |
| New demo acceptance cases | **12 passed**, included in the 630 total |
| Frontend tests | **87 passed**, 0 failed/skipped/cancelled |
| Both TypeScript configurations | Passed, app and node `--noEmit` checks |
| Community and isolated optional Studio builds | Passed; large chunk warnings remain |
| Lint | Passed; two existing AuthContext warnings |
| Existing real Chromium chat journey | **1 passed**, 26 intentionally deselected, 14.44 s |
| Existing real Chromium Community analytics journey | **1 passed**, 6 intentionally deselected, 7.20 s |
| Existing real Chromium isolated Studio evaluation journey | **1 passed**, 6 intentionally deselected, 21.74 s |
| New guarded-demo Chromium acceptance | **Passed**, nine actual public-page screenshots, zero browser runtime exceptions |
| Fresh Alembic upgrade/check | Head `b7a200000001`, no new upgrade operations |
| Restricted current-image production/static/native OCR smoke | Passed; no external provider network |
| Compatibility/dependency/license scope checks | pip check, both npm ls graphs, 18 PDFium notice hashes and default graph isolation passed |
| Advisory metadata | 32/32 Python versions checked, zero reported entries; default npm graph zero reported advisories |
| Credential heuristic / whitespace | Passed; no current-source findings, historical revocation unverified |

The 45/45 deterministic and 7/7 mocked policy evaluations remain a subset of the backend suite; [Step 6 evaluation summary](agent-evaluation.json) keeps them separate from **zero actual Ollama samples**. The new eight-question demo case is additional public synthetic acceptance, not eight real-model tests. Existing backend warnings are Starlette HTTPX TestClient and pypdf add_js deprecations; each browser pytest run has the existing TestClient warning. Optional Studio shows genuine trial notices. No test was silently skipped to obtain these totals.

Twelve new backend cases cover demo target/flag guards, idempotence/refusal of unrelated
data and normal anonymous API acceptance. The acceptance case exercises eight supported
questions with nonempty citations and actual deterministic mode even when LLM is requested.
Seven answered from records; the cross-domain spend-trend question correctly returns
insufficient_evidence rather than inventing a trend. These cases are included in the
full total, not counted twice. [Actual answers](demo-answers.json) contain only public
synthetic response data; dynamic dates/hashes are genuine test output.

The new demo browser check captures [nine genuine PNGs](screenshots/README.md), verifies
actual Community chart/Gantt rendering, expense CSV, cited deterministic chat, private
project 404 and signed-out creation denial. It runs the guarded loopback app without auth
or provider overrides. Separate existing chat/analytics browser journeys use real React,
FastAPI and local PostgreSQL while external providers/models are mocked. Their `llm`
execution label does not prove real model inference. Studio is a permitted local trial
journey only; no Studio screenshot/public entitlement is claimed.

[Machine-readable final results](verification-results.json) record the exact inspected image ID, counts and evidence scope.

## Reproduction on a separate regression DB

The complete suite needs a **fresh migrated, never-seeded** database. Do not reuse the
seeded demo database: older rollback fixtures query the public baseline and require
it empty. With the local fixture from the runbook running, create once:

```sh
docker exec opendev-demo-postgres createdb -U opendev opendev_test_regression_local
export DATABASE_URL=postgresql+psycopg://opendev@127.0.0.1:55438/opendev_test_regression_local
export TEST_DATABASE_URL="$DATABASE_URL"
export APP_ENV=testing
(cd backend && python -m alembic upgrade head && python -m alembic check)
(cd backend && CHECKOUT_ENABLED=true RECEIPT_PROCESSING_ENABLED=true LLM_ENABLED=true python -m pytest -q)
(cd frontend && npm test && npx tsc --noEmit -p tsconfig.app.json && npx tsc --noEmit -p tsconfig.node.json && npm run lint && npm run build)
# Optional, only when local evaluation is installed and permitted:
(cd frontend && ANALYTICS_STUDIO_EVALUATION=true npm run build -- --outDir /tmp/opendev-studio-evaluation)
```

Keep the running demo terminals' original environment. Feature enablement here is
limited to the separate synthetic test process, not a production/public flag change.
After selecting the same regression DB and testing flags, existing browser commands
from backend are:

```sh
PHASE5_BROWSER_JOURNEY=1 python -m pytest -q tests/test_agent_release.py -k complete_public
PHASE6_BROWSER_JOURNEY=1 python -m pytest -q tests/test_analytics_release.py -k real_public
TEST_STUDIO=1 PHASE6_BROWSER_JOURNEY=1 python -m pytest -q tests/test_analytics_release.py -k real_public
python -m pytest -q tests/test_release_journey.py::test_full_cookie_authenticated_release_journey
```

Chromium must be installed. Existing harnesses start loopback-only temporary servers
and close them. The final demo API and frontend both exited 0 on SIGINT; the dedicated test database was stopped with data retained and the original environment service preserved. Their state/cookie/financial/extraction flows are synthetic HTTP test
evidence, not genuine upstream acceptance. Browser wait helpers now wait for the page
body before polling its text, avoiding an initial-document navigation race.

Docker review image reproduction (no public deployment):

```sh
docker build -f deploy/Dockerfile -t opendev-review:phase7-step6 .
python scripts/release-container-smoke.py --image opendev-review:phase7-step6
```

In managed cloud builds use the runtime skill's inherited proxy and mounted public
CA trust; keep TLS verification enabled. This task used the local managed socket and
`--secret id=proxy_ca,src=/etc/ssl/certs/ca-certificates.crt`. The smoke uses synthetic
production settings, no network, one CPU/512 MiB, read-only root, 32 PIDs/64 MiB tmpfs,
UID 10001 and no model weights. It validates health, actual static assets, disabled
upload and digital-PDF/scan/PNG OCR. No Supabase object is required.

## Local measurements

Current image smoke: startup **7.77 s**; native diagnostic **2.77 s**, child CPU **2.24 s**,
maximum individual child RSS **62,400 KiB**, container cgroup peak **175,341,568 bytes**
(167.22 MiB), post-idle **67.89 MiB / 512 MiB**. This is one fixture sample, not hostile
native decoder or worst-case concurrent-upload capacity.

[Current local container sample](local-container-capacity.json): testing-mode startup
**5.05 s**; static root HTTP 200/458 bytes/57.88 ms; 20/20 DB-health requests successful
at concurrency eight, median **20.11 ms**, maximum **34.87 ms**; three retained DB
connections; idle point CPU **0.17%**, memory **69.63 MiB / 512 MiB**; clean shutdown
**0.53 s**, exit **0**. CPU is a point sample, not sustained load. The image has no LLM.

Step 5's separate [application workloads](../phase7-ai-local-capacity.json) remain
historical local evidence: ten requests each, median / empirical-p95 ms:
project 6.57/9.02, combined financial analytics 29.91/55.13, development summary
13.61/20.65, deterministic agent 10.25/12.37, CSV 32.83/65.43; zero errors. With ten
samples this p95 is the maximum, not a production-tail estimate. SQL counts and client
RSS/CPU are in the artifact; none measures a model daemon or Render.

**Real model latency/load/RAM/VRAM/throughput: NOT MEASURED.** Real Ollama inference
NOT RUN; no server or weights were installed or fetched. Free hosted model co-location
is unsupported by available evidence. Deterministic public functionality needs no LLM,
but the inherited release gates still block public deployment.

## Dependency, license and secret scope

`pip check` and root/isolated Studio `npm ls` passed. Default npm registry audit reports
zero advisories in its inspected graph: [summary](npm-advisories.json). Version-specific
PyPI metadata reports zero entries for all 32 inspected Python packages:
[results](python-advisories.json). Neither covers all native/OS packages or guarantees
zero vulnerabilities. No dependency pins or locks changed.

[Inventory](dependency-license-inventory.json) records declarations; all 18 previously
recorded PDFium bundled notice hashes match the installed wheel. Main lockfile excludes
Studio/Enterprise. Application licensing and full notice/native/prior-artifact review
remain open; no root license was invented. See [license notes](license-notes.md).
Current-source credential heuristics found no matches; this does not prove historical
credential revocation, scan ignored private `.env` files or audit upstream logs.

## Failed attempts and evidence limits

The first broad backend run was incorrectly pointed at the seeded demo baseline and
reported **58 failed / 572 passed**. Existing rollback fixtures require a separate
empty baseline; the runbook now explicitly separates the two databases. A subsequent
attempt reported **565 passed / 65 setup errors** when cloud disk space exhausted during
schema creation. Unused Docker build cache was reclaimed without deleting source or
DB volumes; the final suite uses a new fresh migrated local target. These attempts are
not counted as passing evidence. No product restriction was relaxed to hide them.

An initial chat browser run hit a missing-body navigation race; its polling helper
and the equivalent analytics/demo helper were hardened, and final journeys pass.
Early demo-fixture checks exposed missing required linked-evidence metadata and an
artifact-directory setup error; these were corrected before final acceptance. A sandboxed
Node run summarized only four file processes; normal process-access rerun reports the
87 actual tests. Initial npm advisory access was sandbox-blocked; the allowed registry
request succeeded using normal process access. No policy bypass or disabled TLS was used.

Open release gates include historical credential incident closure, whole-app licensing,
true decoder isolation/quotas, hosted HTTPS OAuth/cookies/logs, real Sandbox/webhook/storage,
historical refund coverage, target free capacity/restore, real model quality if offered,
optional Studio rights and broader beta/mobile/CI/native-spreadsheet acceptance.
Public deployment remains **NO-GO**. Video, organizer rule check, judge-accessible
repository/video links and actual form submission remain owner work.
