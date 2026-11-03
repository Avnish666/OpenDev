# Phase 5 Step 6: agent evaluation and release readiness

Assessment: 2026-11-03, Asia/Calcutta. **NO-GO for public deployment.** GO for
continued local development with synthetic data. No paid API, model download,
financial write, production migration, deployment, commit or push was performed.
This is a scoped review with reproducible tests, not a penetration-test certificate.

## Architecture reviewed

React public project details lazy-load ProjectAIChat. Its single-question POST goes
to the existing FastAPI worker, bounded admission and REPEATABLE READ / READ ONLY
snapshot. Seven allowlisted public evidence tools reuse deterministic accounting,
immutable roadmap history, GitHub snapshots and owner-only public credibility.
Ollama receives JSON projections and schemas, never a database/session or unrestricted
executor. Dispatcher names/arguments/project/owner pins are code-enforced independently
of model instructions. No model operation can approve expenses, capture/refund money,
change rewards, certify delivery or execute SQL/shell/HTTP/filesystem tools.

The model chooses exact scalar fields or strict financial/development templates.
Server code owns monetary values, deadline arithmetic, permitted relationships and
citations. Deterministic mode requires no provider. Auto may fall back; returned
execution_mode controls the UI label. Provider credentials, prompts, private OCR,
receipt storage paths, backer identities and reviewer notes are not public evidence.
Questions/transcripts are not persisted by application code; optional test reports
below contain synthetic fixture questions only, not application request logging.

Reviewed sources include all five preceding Phase 5 guides, Phase 4 release review,
actual provider/dispatcher/routers/templates, public accounting/roadmap/credibility
projections, typed React client/citation mapping and the existing test infrastructure.

## Confirmed defects and fixes

| Finding | Evidence | Fix / disposition |
| --- | --- | --- |
| Medium availability: initial snapshot/fallback failures escaped the model-loop handler | New regression cases raised TimeoutError and OperationalError during EvidenceTools construction; before the fix both propagated instead of producing an agent result. | Router catches database/time-budget errors after snapshot cleanup, returns controlled insufficient_evidence, withholds SQL/driver details, and releases admission. No reads are retried on an aborted transaction. |
| Low functional: unsupported suggested funding question | The real browser submitted “How much funding has this project received?”; deterministic intent matching accepted “the project”, so the displayed suggestion returned Unsupported question with no citations. Mock frontend fixtures had hidden the mismatch. | Align the suggestion and browser regression with the supported canonical phrase. The real project-page suggestion is submitted by keyboard and must return the seeded funding/citation. No semantic routing/product feature was added. |

No critical authorization bypass or financial mutation was confirmed in this scoped
review. The tests do not establish absence of undiscovered vulnerabilities.
Test harness corrections were also needed: real signed-out auth replaces a fixture
that returned None as an authenticated User; response waits synchronize on rendered
answers; the artificial slow-provider response now has a finite terminal turn.
Those are test fixes, not additional product vulnerabilities.

## Evaluation results and artifacts

The existing financial and development datasets are extended with actual outcome
recording, plus seven mocked-model policy evaluations. Artifacts are checked in:

- `phase5-evaluation-results.json`: case ID, expected facts/citations/forbidden claims/
  statuses, actual answer/status/mode/source facts/citations, pass/fail reason.
- `phase5-performance.json`: measured per-sample latency, SQLAlchemy statement count,
  response size, evidence count, model-dispatch calls, fallback flag and environment.

Results remain separated by provider:

| Evaluation | Result | Meaning |
| --- | --- | --- |
| Deterministic financial scenarios | 15/15 passed | Exact expected source facts, citation hashes, statuses and privacy/forbidden-claim assertions |
| Deterministic development scenarios | 30/30 passed | Original/revised deadlines, timing, history, stale/missing GitHub, ownership/rewards and cross-domain limitations |
| Mocked model-boundary scenarios | 7/7 policy checks passed | One accepted grounded finance answer; six intentional rejection/outage cases safely returned deterministic fallback |
| Real Ollama semantic/inference evaluation | **Not run** | No model/server/version/quality or live tool-call success claim |

The mocked plausible wrong amount is 2100 against a real recorded 2000; other
responses attach plausible but unsupported completion, causation or misuse prose
to otherwise valid citations. Invented references are also rejected. A real
reference cannot authorize extra model-provided figures or explanations. These are
strict schema/grounding checks, not an accuracy percentage for a neural model.
The six fallbacks out of seven are deliberately injected, not a natural failure rate.

Optional pytest artifact recording is enabled only by PHASE5_RESULTS_DIR. No external
reporting/analytics service is introduced. Generated IDs/hashes identify one local
run; later fixture IDs and calculation timestamps may differ. Reproduce facts and
current-request citation relationships, not old hashes as if they were an archive.

## Hallucination, injection and privacy review

Existing and new regressions cover invented amounts/deadlines/statuses/GitHub facts,
unknown and foreign citations, cross-project and unrelated-owner requests, partial
refund limitations, private receipt exclusion, misleading completion and causal
claims, prompt-sized bodies, response/context/call/turn limits and repeated loops.

Fifteen new adversarial combinations embed instructions in public project, expense,
milestone, issue or PR text, then have the mock provider request SQL, private receipts
or another project's finances. Only the legitimate first source call executes;
second calls are rejected by the dispatcher and answers fall back safely. Existing
privacy tests cover signed-out and owner access, draft/non-active denial, originals,
private OCR/reviews, backer notes and read-only SQL rejection. Financial/milestone
source-state snapshots remain unchanged across the integration journey.

**Semantic validation remains limited.** Scalar values are exact projections, and
financial/development templates constrain known relationships, but a model can
select irrelevant/cherry-picked facts or quote misleading source text. Citation
existence/hashes do not prove relevance, source authenticity, completeness, personal
honesty, vendor payment or causality. No free-form model explanation is treated as
authoritative evidence. New maintainers get insufficient history; GitHub closure/
merge never establishes delivery. Bounded/deleted/sampled observations cannot prove
abandonment, trends or complete repository activity. These limits remain in answers
and are still deployment concerns pending real-model adversarial evaluation.

## End-to-end/browser acceptance

The new opt-in journey starts the **actual React application**, local FastAPI and
migrated isolated PostgreSQL. Only external GitHub/model responses and a single
transient error are mocked. It exercises public project navigation, lazy chat,
keyboard submission of the actual funding suggestion, real financial retrieval,
source link expansion/opening and authorized source GET, mocked model selection
of both roadmap/GitHub tools, citations/limitations, unsupported status, retry after
503, Auto fallback, Cancel/Clear, 390px layout, polite announcement hooks and three
round trips through real project/explore routing. Stored financial/reward/milestone
state is compared before/after. Private original/extraction IDs never enter answers.

The existing mock-API Chromium suite additionally exercises malicious HTML, unsafe
URLs, stale/missing citations, provider states, 429 cooldown, repeated submission,
clear during pending work, late response suppression, visibility-denial cleanup,
mode labels, no transcript storage, mobile overflow and unmount cleanup.
Both browser runs passed. These are Chromium functional/accessibility-hook checks,
not an NVDA/VoiceOver audit, broad browser certification or hosted HTTPS acceptance.

Cancellation is deliberately qualified: an explicit backend cancellation signal
closes a waiting provider coroutine and releases all four worker slots (new test).
The development proxy can retain an upstream request after the browser aborts; its
slow mocked response was allowed to finish within its bounded window before cleanup.
Browser abort alone is not proof GPU inference stopped. Validate disconnect forwarding
and backend shutdown under the actual production proxy. Resource/DB operations remain
cooperative between statements; pool acquisition, OS memory and blocked sockets are
not hard process-isolation guarantees.

## Local performance

Environment: Debian 13 Linux, Python 3.12.14, Node 24.19.0, npm 11.9.0,
Chromium 154.0.8037.57, local PostgreSQL 16 Docker, five visible CPUs. Each workload
has three sequential TestClient samples using one active project, one milestone,
one 2000-cent completed contribution and one 1000-cent published expense. No real
model, network storage or hosted provider is measured.

| Workload | Median request latency | SQLAlchemy statements | Response bytes (first sample) | Evidence envelopes |
| --- | --- | --- | --- | --- |
| Deterministic funding | 14.298 ms | 9 | 4537 | 1 |
| Deterministic development | 17.509 ms | 12 | 6178 | 1 |
| Deterministic funding + schedule | 20.640 ms | 17 | 10779 | 2 |
| Auto, forced provider outage | 10.522 ms | 9 | 4574 | 1 |

SQL counts exclude driver-level statement_timeout controls and BEGIN/COMMIT; they
are not total wire SQL counts. Deterministic requests make zero model dispatches;
this does not mean zero evidence reads. The forced outage fell back in 3/3 samples.
Mocked accepted model answers use one financial call; the browser development model
uses two approved calls (roadmap and GitHub). No unauthorized attack call succeeds.
Peak pytest RSS at the benchmark point was **204596 KiB**, cumulative test-process
memory, not incremental service memory, browser/DB RSS or a production-worker bound.
GPU memory and real model latency were not measurable. Three synthetic local samples
are neither throughput/load percentiles nor evidence that Render Free can host this.

Four worker slots and memory-only peer/global rate quotas remain process-local.
Snapshots/connections can stay open while waiting for inference. Large histories and
profiles may hit materialization, tool/context/answer limits. Actual free-tier CPU,
RAM, queue/pool saturation, distributed admission and adversarial load tests remain
required; no Redis/paid infrastructure or hidden hosted performance claim is added.

## Ollama compatibility and local reproduction

Official native API types and Python tools example were retrieved from:
[api/types.go](https://github.com/ollama/ollama/blob/main/api/types.go) and
[examples/tools.py](https://github.com/ollama/ollama-python/blob/main/examples/tools.py).
Checked fields include POST /api/chat model/messages/tools/stream/options/think,
assistant tool_calls[].function.{name,arguments,index}, object arguments, tool-role
content/tool_name, final message/done and POST /api/show capabilities. The provider
uses cancellable HTTPX requests, bounded response bytes and model/total deadlines;
wire-format, timeout, outage and multi-turn mocked tests pass. The native API is
unversioned; no actual runtime version is inferred from a main-branch document.
Retrieved type-source SHA-256:
`8e54520d34c312bb6adfccb652b0d1e18bb5c4cdb8ac2eb2eab0c065a508effa`.
Example-source SHA-256:
`dd3e55db866adaf0318728162890911ad6dfebb81399f31d6337e573ebfabdfb`.

No OLLAMA_BASE_URL/OLLAMA_MODEL binding was present; no ollama binary or GPU utility
was found. Existing localhost:11434 /api/version probe failed with ConnectError.
The qwen3:4b catalog request was denied HTTP 403 by this environment's proxy policy.
Therefore current catalog availability, actual model/tag/quantization, server version,
live function calls, live citation acceptance and inference RAM/VRAM remain
**unverified**, not passed. No weights or server were installed. Upstream Qwen
sources reviewed in Step 2 identify 4B/tool support; that does not validate a current
mutable Ollama catalog tag. No paid provider is necessary for deterministic use.

On a developer machine, explicitly install a supported Ollama release from its
official source, verify current qwen3:4b tag/license and capacity, then manually run:

```sh
ollama --version
ollama serve                       # keep on loopback, or reuse an existing server
ollama pull qwen3:4b                # explicit operator download after catalog verification
ollama show qwen3:4b
curl http://localhost:11434/api/version
curl http://localhost:11434/api/show -d '{"model":"qwen3:4b"}'
# Require tools capability and record actual model/quantization/version.
cd /workspace/OpenDev/backend
source /workspace/opendev-setup/local-env.sh  # only isolated local opendev_test_* DB
export OLLAMA_BASE_URL=http://localhost:11434 OLLAMA_MODEL=qwen3:4b
python ../scripts/agent-ollama-smoke.py --project-id <active-synthetic-id>
```

Record actual execution_mode=llm, status, tools, citations, elapsed request/model
latency, `ollama ps` and GPU/process memory. Repeat a multi-source development question;
compare every number/date/status to cited projections. A fallback is not live model
success. Use reviewed timeout/context settings when cold-start inference exceeds
15 seconds. Cloud/Render localhost is not a developer laptop. No unauthenticated
public Ollama port, automatic request-time download or proxy bypass is authorized.

## Reproduction and remaining release gates

From backend/ with isolated local DATABASE_URL and TEST_DATABASE_URL:

```sh
PHASE5_RESULTS_DIR=/tmp/opendev-phase5-audit APP_ENV=testing python -m pytest -q
PHASE5_BROWSER_JOURNEY=1 APP_ENV=testing python -m pytest -q -s tests/test_agent_release.py -k complete_public
python -m alembic upgrade head
python -m alembic check
```

From frontend/: `npm test`, `npx tsc -b`, `npm run build`, `npm run lint`,
`node tests/browser-chat-smoke.mjs`. The real journey Node script is started by its
pytest bridge, which supplies ephemeral backend/project configuration; it should
not be pointed at a production API. No hosted CI job was triggered.

| Gate | Current disposition |
| --- | --- |
| PyMuPDF/MuPDF AGPL obligations | Open. Pinned 1.26.7 remains AGPL/commercial dual-licensed; no authorized licensing/distribution decision or replacement was supplied. |
| Untrusted file isolation | Open. Resource-limited parsers are not an OS exploit sandbox; hostile-file, concurrency/ingress and target-host acceptance remain required. |
| Historical credential exposure | Open. No secret/history values were read or used. Owner evidence of rotation/revocation and incident review remains necessary. |
| Live PayPal Sandbox | Open. Synthetic tests do not verify real sandbox buyer/capture/signature/refund/reversal flow. No live payments performed. |
| Live Supabase private storage | Open. Bucket isolation, real redaction, signing/expiry/revocation and cleanup remain unverified. |
| Ollama availability/connectivity/quality | Open. No installed server/model; catalog blocked; no live inference or GPU capacity evidence. |
| Render Free / Neon capacity | Open. Current quotas, RAM/CPU, cold starts, long requests, model placement and DB pool behavior are not proven by local measurements. |
| Cross-domain cookies/proxy | Open. Local same-origin proxy is tested; production HTTPS Secure/SameSite/CORS/CSRF and disconnect forwarding are unverified. |
| Exact partial-refund ledger | Open. Conservative full capture exclusion remains; exact refund amounts are unavailable. No financial rewrite was made. |
| Bryntum beta compatibility | Open. Existing pinned Community beta/local browser coverage does not resolve long-session, broader-browser, bundle/mobile or target-host acceptance. |

**Recommendation: NO-GO for deployment; GO for continued isolated development.**
No inherited gate was closed without evidence. Real-model adversarial acceptance,
semantic relevance, production resource isolation and the above service/legal gates
remain outstanding.

## Final check totals and changed files

- **407 backend tests passed, 0 failed/skipped**, 231.87 seconds, plus **one passed
  opt-in real browser variant** of the existing integration test (13.59 seconds).
- **55 frontend tests passed, 0 failed/skipped**. TypeScript, production build,
  lint and both Chromium journeys passed. Two existing AuthContext warnings and
  the large lazy Gantt warning remain. Existing Starlette/HTTPX warning remains.
- **45 deterministic + 7 mocked-model policy evaluations passed**; a focused
  seven-case rerun additionally captured actual tool/turn/latency diagnostics.
  Correct mocked output used one financial tool/two model turns; malformed/invented
  conclusions fell back after one approved retrieval; outage performed no model tools.
- Alembic upgrade/check passed without drift, head `8c6072dabc59`; compilation,
  whitespace, dependency compatibility and API response contract tests passed.
- Live Ollama: **not run**. Hosted service/legal/capacity acceptance: unverified.

Product changes: `backend/app/routers/agent.py` controlled snapshot failure handling;
`frontend/src/components/ProjectAIChat.tsx` canonical supported funding suggestion.
Test/report changes: new `backend/tests/test_agent_release.py`, optional artifact
hook `backend/tests/conftest.py`, outcome instrumentation in financial/development
scenario tests, new `frontend/tests/browser-agent-journey.mjs`, matching canonical
suggestion in `browser-chat-smoke.mjs`, this report and the two JSON artifacts.
No authoritative financial/payment/reward/milestone service, dependency, schema or
migration was changed. No production operation, commit or push was performed.
