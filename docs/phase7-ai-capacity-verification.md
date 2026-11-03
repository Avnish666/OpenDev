# Phase 7 Step 5: AI inference and hosting capacity verification

Assessment: 2026-11-04, Asia/Calcutta. **NO-GO for public deployment. Real Ollama inference: NOT RUN.** No model/runtime install, weight download, public model endpoint/tunnel, paid API, production migration, financial operation, feature enablement, commit or push occurred.

## 1. Repository state and changed files

Initial `main` HEAD was `fc8fef0` (`Phase 7 Step 4 done`) with a clean working tree. The request's statement that recent work was uncommitted was stale: Step 4 had already been committed/pushed. Its provider diagnostics, secure defaults and 595-test baseline are present. Initial/final whitespace/current-source checks pass; all existing work is preserved. No applied migration, financial calculation, dependency pin or lockfile changed.

Changes: provider configuration/message validation in `backend/app/agent/providers.py`; new loopback-only runner `backend/app/acceptance/ollama.py` and `scripts/ollama-acceptance.py`; `scripts/agent-evaluation-summary.py`; reusable image/database/output selectors in `scripts/deployment-capacity-smoke.py`; new `backend/tests/test_ollama_acceptance.py` and `test_agent_capacity.py`; runtime/evaluation/capacity artifacts, this report and release/deployment documentation links. The existing `scripts/agent-ollama-smoke.py` remains for compatibility; use the new explicit-selection runner for new acceptance work because it validates selectors before importing application configuration and reports missing runtime without a raw traceback.

## 2. Runtime detection

[Runtime evidence](phase7-ollama-runtime.json): configured/default loopback metadata probe returned **unavailable**, no model selected/present, no tool capability verified. `ollama` and `nvidia-smi` executables were not found. GPU/VRAM availability is unverified, not assumed absent or sufficient. No runtime/version/weights were installed or fetched. No local server, model, quantization, load time, token throughput or model RAM/VRAM measurement exists to report.

The probe uses the operator's OLLAMA_BASE_URL/OLLAMA_MODEL if supplied, otherwise loopback `127.0.0.1:11434` and **no guessed model**. CLI accepts only localhost/127.0.0.1/::1, validates ports/model syntax, refuses credentials/query/path/fragment and known cloud-routed tags, does not follow redirects or use ambient proxy/cookies, and uses bounded metadata reads. It only GETs version/tags and POSTs show for an already listed exact model. It never calls pull/create/delete or exposes a listener. Remote-model metadata prevents inference acceptance. Runtime probe evidence is distinguished from injected mocked detection.

## 3. API/model compatibility

The application provider uses Ollama `/api/show` tools capability, `/api/chat` nonstreaming, `think=false`, bounded generation/context options and five-minute keep-alive. It appends assistant tool_calls followed by role=tool/tool_name/content messages with structured public evidence. Function names/arguments are validated separately from the model; unknown names, extra arguments, cross-project/owner IDs and wrong types fail. Native Ollama argument objects are required; arbitrary JSON strings are not silently coerced to force compatibility.

The adapter now catches malformed endpoint brackets/ports as sanitized ProviderError, validates model names and checks output size before copying into the parent buffer. It requires an explicitly assistant-role message: an omitted role previously inherited a schema default instead of proving wire compatibility. Existing per-request async wall/HTTP limits and maximum response/context/tool/turn budgets remain. Invalid payloads are never forwarded verbatim.

These are protocol/source/mock compatibility findings, not proof that a particular installed model follows the contract. qwen3:4b is only a candidate: its exact tag, license, quantization, tools support, disk and RAM must be verified on the developer's machine. No automatic large download was authorized or performed.

## 4. Actual inference/tool-chain results

**Zero actual inference samples.** Financial, expenses, budget, roadmap, GitHub, maintainer, rewards and cross-domain real model→validated tool→DB evidence→model→grounding→frontend sequences are NOT RUN. There are no genuine model tool names/counts/latencies to claim.

The future runner attempts eight domains only after explicit `--execute-inference`, an installed local tool-capable exact tag, APP_ENV=testing, LLM_ENABLED=true and a positive synthetic project ID. DATABASE_URL must be an isolated loopback `opendev_test_*` PostgreSQL target. Host/service overrides are rejected; the benchmark pins libpq hostaddr and connection timeout. It uses public EvidenceTools inside read-only snapshots/database budgets, never model-written SQL or application write tools. It records only status, actual mode, validated tool names/turns, citation count/integrity, SQL count, latency and whitelisted provider timing/token counters. Raw prompts, source text, arguments, model prose and private records are withheld.

A valid model message establishes that a real endpoint responded, not semantic correctness. A fallback is not a model answer. Runner pipeline checks require answered/llm, actual authorized tool use and citation integrity, but **semantic review remains required**. The eight-domain benchmark uses an owner-prepared synthetic project, not automatically all seeded reference-dataset scenarios. Full live evaluation of the existing per-seed reference datasets remains a separate operator task once a model exists.

## 5. Deterministic versus mocked versus actual evaluations

The unchanged reference datasets (`financial_agent_evaluation.json`, `development_agent_evaluation.json`) and mocked policy scenarios were rerun with the full suite. Their expected facts, exact numbers, citation hashes, privacy/forbidden claims and status assertions remain authoritative test oracles. Development fixtures use a fixed evaluation instant; do not confuse that with live GitHub freshness.

[Evaluation summary](phase7-ai-evaluation.json) reports separate provider classes. Application `execution_mode=llm` in a Replay/MockTransport test does **not** establish real inference. Summary generation strips answers/source text and never promotes an execution label into a real-provider claim. Actual Ollama table has n=0/NOT RUN.

| Evaluation source | Samples | Passed | Failed | Specific failures |
| --- | ---: | ---: | ---: | --- |
| Deterministic reference cases (15 financial, 30 development) | 45 | 45 | 0 | None observed |
| Mocked model policy scenarios | 7 | 7 | 0 | None observed |
| Actual Ollama | 0 | — | — | NOT RUN; runtime/model unavailable |

These 52 cases are a subset of the 618 backend tests, not additional tests.

The live runner is not an automated semantic oracle. To extend the reference dataset later, seed a new disposable schema for each existing case using the same fixture helpers, run that case against actual Ollama (no Replay), compare expected facts/required claims/forbidden phrases/source references and capture actual mode. Keep date-fixed development evaluation distinct from current-time inference. Record failures, irrelevant-but-valid selections and fallback frequency; do not report fallback correctness as model success.

## 6. Security findings

Confirmed safe-to-fix provider defects: malformed endpoint ports/brackets could escape the intended sanitized configuration path; assistant role omission was accepted through a default; oversized chunks were copied before the byte check. Narrow fixes and 22 new detection/configuration/wire tests cover these paths. No code-execution or unauthorized-write exploit is claimed.

Existing source-injection matrix covers project/expense descriptions, milestone descriptions and issue/PR titles with attempts at SQL, private receipts and cross-project tools. PR bodies/descriptions are not retained in the current evidence contract; future body ingestion needs its own adversarial acceptance rather than a claim it was tested live. Other suites reject shell/write/secret tools, extra arguments, fabricated citations, wrong facts/currencies/dates, inferred fraud/causation and unsupported delivery assertions. Tool authorization, public source selection and read-only DB transactions are enforced outside the model. Private receipt/OCR/review/backer fields are not model evidence. No write-capable tool was added.

Model cancellation tests verify pending provider work closes and worker slots release. Concurrent-user admission is bounded per worker; distributed quotas, connection-pool waits, OS memory and blocking work are not a hard global sandbox. Actual server shutdown **during real inference** is NOT RUN; Docker stop and mocked cancellation are different evidence. Runtime endpoint configuration is operator-controlled, never a model/user tool argument, with redirects and ambient proxy use disabled. A future remote provider still requires an approved private/authenticated network design; this code adds no remote credentials or public gateway.

## 7. Grounding limits

Citation existence/hash integrity proves provenance of selected current evidence; it does not prove relevance to the question or completeness of source records. A model can select the wrong but authentic scalar or template. Typed claim templates reject extra numerical/causal prose and backend code renders source values/formulas; authoritative financial arithmetic remains deterministic even when the model selects tools/claims.

No receipt alone proves payment; recorded Sandbox funding is not a bank balance; exact historical unknown refunds remain NULL/conservatively excluded; delivery is a maintainer assertion; retained GitHub evidence is incomplete and ownership is not authorship. These limitations remain in answers. No live-model semantic accuracy or resistance rate is claimed from replay tests. Keep deterministic public defaults until real, per-case semantic/authorization acceptance has evidence.

## 8. Model resource results

| Metric | Actual model result |
| --- | --- |
| Server/model/quantization | NOT RUN / none verified |
| Load time / first token / response latency | Not measured |
| Daemon peak RAM / GPU peak VRAM / model CPU | Not measured |
| Token throughput / inference concurrency / timeout frequency | Not measured |

The optional runner records load/eval/prompt/total nanosecond counters and tokens/second only if the actual endpoint supplies valid counters. Nonstreaming requests cannot measure first-token latency; that field stays null. `benchmark_process_peak_rss_kib` is the CLI/test process, **not Ollama daemon memory**. GPU and daemon peaks stay null unless separately monitored; do not substitute client RSS or configured cgroup limits.

## 9. Local application capacity

[Local capacity JSON](phase7-ai-local-capacity.json) is an actual synthetic PostgreSQL/TestClient sample. It covers project GET, combined financial/development analytics overview, progress summary, deterministic agent query, financial CSV, a small concurrent read batch and one deliberately mocked provider-outage fallback. No real LLM participates. Per workload n=10; median and empirical p95 are recorded. With ten samples empirical p95 is the maximum, not a production-tail estimate. SQL statement counts exclude driver-level control statements; process CPU excludes PostgreSQL/model CPU. RSS is cumulative pytest process peak, not incremental web-server or model RSS.

| Local workload | n | Median ms | Empirical p95 ms | SQL/request | Response bytes | Errors |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| project | 10 | 6.57 | 9.02 | 3 | 409 | 0 |
| financial_analytics | 10 | 29.91 | 55.13 | 31 | 33564 | 0 |
| development | 10 | 13.61 | 20.65 | 17 | 4601 | 0 |
| agent_deterministic | 10 | 10.25 | 12.37 | 9 | 5001 | 0 |
| csv | 10 | 32.83 | 65.43 | 31 | 3698 | 0 |

Concurrent project reads: 12 requests/four workers, zero errors, median 23.08 ms, maximum 33.92 ms. Workload client/test CPU 0.839 s; cumulative pytest RSS 138,860 KiB. One mocked auto-provider outage returned actual deterministic mode. No actual LLM workload ran.

The Docker image contains the web app, English OCR and static Community assets, **no Ollama binary or weights**. Startup, disabled-upload/static serving and native OCR smoke run under one CPU/512 MiB/read-only root/no-network/32 PIDs/64 MiB tmpfs. Application cold-start/clean-stop/concurrent DB measurements from Step 3 remain historical evidence; actual Step 5 smoke values are recorded below.

A separate [current-image container sample](phase7-ai-container-capacity.json), using testing-mode local PostgreSQL with checkout/receipt/LLM flags false, recorded startup **3.09 s**, static root 200/458 bytes/63.70 ms, **20/20 DB-health requests successful** at concurrency eight, median **24.18 ms**, maximum **42.59 ms**, three retained DB connections, idle point CPU **0.18%**, memory **69.51 MiB / 512 MiB**, clean stop **0.61 s**, exit **0**. This uses synthetic plaintext local PostgreSQL and a chosen local cgroup; it is neither production TLS/Render evidence nor a sustained CPU peak. Shutdown during actual inference remains untested. The temporary app containers were removed and the Step 5 PostgreSQL fixture stopped without removing its data; the original environment PostgreSQL service was preserved.

To repeat this current-image sample after building the image and starting the dedicated local PostgreSQL fixture, choose a **fresh** name (existing DB creation fails safely) and output artifact:

```sh
python scripts/deployment-capacity-smoke.py --image opendev-review:phase7-step5 \
  --database opendev_test_phase7_step5_capacity_repeat \
  --output /tmp/phase7-step5-capacity-repeat.json
```

The script accepts only opendev_test_* names, uses the dedicated local fixture and exposes the temporary app only on loopback. It creates no tables/financial records and removes only its own app container; databases are retained. No local measurement establishes Render latency/capacity.

## 10. Render Free feasibility and network requirements

The application works without an embedded LLM: production LLM_ENABLED defaults false and deterministic public evidence remains useful. Existing synthetic Docker proof runs in a chosen 512 MiB local cgroup; this is **not** a statement of current Render Free quotas. No GPU, model placement, free-host capacity or live hosted measurement was established. Provider documentation/current plan acceptance remains owner work.

A hypothetical four-billion-parameter four-bit model needs roughly 2 GB of raw weight storage alone, excluding metadata, runtime/KV cache, context, OS and web processes. This is a theoretical lower bound, not a measured qwen3:4b size or a current Render plan claim. It already exceeds the tested 512 MiB web profile. There is no evidence to recommend cohosting that model in the free web container or downloading weights at startup.

Recommended zero-budget path: deterministic public candidate (still NO-GO for the other gates), separate **local** AI demonstration on owner hardware with approved installed weights. Remote inference is optional future work: private reachable network, TLS/trust, strict backend authentication or private network identity, backend-only credential handling, bounded requests, outage policy and zero-budget terms must be verified. The existing Ollama adapter has no public gateway API-key integration and must not be exposed unauthenticated through a public tunnel. A paid provider is not a release prerequisite. Render localhost cannot reach a laptop's localhost; do not weaken network/auth controls to bridge it.

## 11. Failure and degraded modes

- LLM_ENABLED=false overrides client llm/auto requests to deterministic and declares that actual mode; no model initialization occurs.
- Enabled auto mode + unavailable/missing/timed-out provider falls back deterministically if a safe DB transaction and time budget remain.
- Enabled llm-only provider outage returns provider_unavailable, not an answered model result. The requested path label alone is not evidence that a model ran.
- Invalid tool calls, repeated calls, context/response overflow or unsupported claims yield validated deterministic fallback where safe or explicit insufficient evidence; modes/limitations remain truthful.
- Cancellation propagates and releases slots/connections; SQL-aborted snapshots do not perform fallback queries. These are tested cooperative bounds, not process-isolation guarantees.
- Existing React actual-mode indicator/cancellation/retry/citation rendering tests and PostgreSQL-backed chat journey remain; real-model browser end-to-end is NOT RUN.

## 12. Regression and browser results

| Check | Actual result |
| --- | --- |
| Complete backend suite | **618 passed**, two existing deprecation warnings, 332.78 s |
| New local probe/provider guards | 22 cases included above |
| New local workload benchmark | One case included above |
| Frontend tests | **87 passed**, zero failed/skipped |
| Both TypeScript configurations | Passed (`tsc --noEmit -p tsconfig.app.json` and `tsconfig.node.json`) |
| Lint | Passed; two existing AuthContext warnings |
| Community / isolated optional Studio builds | Both passed; large chunk warnings remain |
| Fresh local PostgreSQL migrations | All revisions to `b7a200000001`; Alembic check: no new upgrade operations |
| Real Chromium, chat | One passed / 26 deselected, 17.46 s |
| Real Chromium, Community analytics | One passed / six deselected, 9.67 s |
| Real Chromium, isolated Studio analytics | One passed / six deselected, 21.16 s |
| Docker production/OCR smoke | Passed; synthetic configuration, no external network |
| Current-source credential heuristic / whitespace | Passed; no current findings; historical incident remains open |

Browser journeys exercise real React/API/local PostgreSQL with external providers **mocked**. Optional Studio's local trial banner does not confer public distribution rights. No hosted CI run, actual hosted OAuth/provider acceptance or live-model browser success is claimed. No live model result is treated as a local or mocked pass. Existing startup/feature-disabled tests remain, along with tool/citation/failure/cancellation/concurrency/privacy regressions.

Image `opendev-review:phase7-step5`, SHA-256 `5755503ae78333bb6fd608e85ae56f2fd5375c10065e6d92e174cd098517959b`: synthetic production startup **7.73 s**; static assets and disabled-upload 503 verified; digital PDF, scan PDF and PNG OCR passed (12.34 USD fixture). Native diagnostic **2.40 s**, child CPU **1.96 s**, maximum individual child RSS **62,456 KiB**, whole-container cgroup peak **176,345,088 bytes** (168.18 MiB), post-idle **68.59 MiB / 512 MiB**. This is one diagnostic sample, not a worst-case decoder/concurrent-upload capacity proof. The app contains no model runtime/weights.

## 13. Exact future local commands

These are **manual developer instructions**, not actions taken in this cloud task. Install a trusted Ollama distribution from the official vendor only after reviewing it. No installer or large download ran here. Use existing installed weights first:

```sh
OLLAMA_HOST=127.0.0.1:11434 ollama serve
# another terminal
ollama --version
ollama list
ollama show qwen3:4b --license
ollama show qwen3:4b
```

If that exact model is absent, stop and obtain explicit approval for its current download size, license and RAM/disk requirements before manually running any pull. Do not select a cloud-routed tag to bypass local limits. Official references for owner verification: https://docs.ollama.com/api and https://docs.ollama.com/capabilities/tool-calling and https://ollama.com/library/qwen3:4b ; current weights/terms were not independently verified here.

Metadata-only probe (never pulls/loads a missing model):

```sh
python scripts/ollama-acceptance.py --environment local-test --model qwen3:4b
```

Prepare/migrate a **fresh local** opendev_test_* PostgreSQL DB and synthetic active project, never production data. Reuse existing fixture helpers/reference seeds; record the project ID and any scoped synthetic schema. DATABASE_URL must identify that local DB; allowed query options are limited to the synthetic search_path form. Explicitly select the approved test configuration without printing its URL:

```sh
export APP_ENV=testing
export LLM_ENABLED=true
export OLLAMA_BASE_URL=http://127.0.0.1:11434
export OLLAMA_MODEL=qwen3:4b
# Inject DATABASE_URL for the approved local synthetic DB through local test setup.
python scripts/ollama-acceptance.py --environment local-test --model qwen3:4b \
  --project-id <synthetic-active-id> --execute-inference --samples 1 --concurrency 1
# Optional explicitly selected second run: --samples 2 --concurrency 2
```

Positive project ID is required; do not paste angle-bracket placeholders literally. Maximum CLI concurrency is two and repetitions three; each question has bounded model/DB/context/tool budgets. There is no automatic unsafe feature enablement or database seeding inside the inference runner. It refuses production environments and host/service DB overrides. Keep checkout/receipt flags off for a local demonstration when not needed. The model receives public read-only tools only.

For a local browser demo, run FastAPI on loopback and the existing Vite same-origin API proxy with a matching trusted FRONTEND_URL; use synthetic projects and keep all model networking private. Verify the actual Ollama backend responds and then test the chat/citations without Replay. Do not run a public tunnel. A live frontend success is separate from CLI inference checks.

Monitor the **daemon/runner**, not just the benchmark client: identify its PID/cgroup, collect baseline/peak RAM and CPU during loading/generation, and use a GPU monitor such as nvidia-smi only if a GPU exists. `/usr/bin/time` around the CLI measures client resources, not the separate model service. Record installed model/quantization/server version, cold/warm load, first-token only with an explicit streaming measurement, response/tokens, concurrency/errors and shutdown behavior. Store redacted summaries only.

Reproduce local existing evaluations with PHASE5_RESULTS_DIR set while running pytest against a migrated local test DB, then summarize without transcripts:

```sh
python scripts/agent-evaluation-summary.py --input <private-results-dir>/phase5-evaluation-results.json \
  --output docs/phase7-ai-evaluation.json
```

## 14. Remaining blockers

P7-09 real model availability, semantic relevance/quality, model rights and private hosting remain open. So do owner credential rotation/incident review, application distribution rights/notices, true OCR isolation/quotas, current free-host/DB capacity and restore, HTTPS OAuth/proxy/logging, genuine Sandbox/webhook/Supabase acceptance, historical refund coverage, limited-tier uncertainty, native spreadsheet and beta/mobile/CI/native security acceptance. Optional Studio has no public licensing evidence. No other blocker is closed by these local AI tests.

## 15. Phase 7 Step 6 prerequisites

For isolated continuation, preserve/review this uncommitted work and assign evidence owners to open gates. If a real AI demo is required, supply an approved already-installed local tool-capable model, synthetic local DB, explicit testing/LLM opt-in and a resource/semantic evaluation plan; otherwise retain deterministic mode and report AI inference unavailable. Before any public host or target migration, require separately approved concrete deployment/backup/restore settings, credential and licensing evidence, actual containment/free-capacity and provider/HTTPS acceptance. Do not silently enable flags, paid endpoints or model downloads to meet a milestone.

## 16. GO / NO-GO

**NO-GO for public deployment; GO for isolated review and deterministic demonstration.** There was no real Ollama inference and no model-resource measurement. Useful deterministic functionality does not require a hosted LLM, but that does not clear the inherited release blockers. No commit, push, public endpoint, paid API or production action occurred.
