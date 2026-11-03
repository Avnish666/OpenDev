# Phase 5 Step 2: bounded LLM tool orchestration

**Deployment remains NO-GO.** This step does not close Phase 3/4 release gates,
introduce financial decisions, modify records, add tables, download models, deploy,
commit or push. No paid API, framework or new dependency is required.

## Architecture and files

The existing public POST `/api/projects/{id}/agent/query` accepts optional `mode`:
`deterministic`, `llm`, or `auto`. Omission uses `AGENT_MODE`, default deterministic.
The body still requires matching `project_id` and a 3–1,000 character question.
Existing answer fields remain; additive fields are `execution_mode`,
`source_freshness`, and safe `diagnostics` (executed tool names, model turn count,
latency in milliseconds). `provider_unavailable` is an additional answer status.
No prompts, provider response bodies, provider URLs or chain-of-thought are exposed
in diagnostics. Public evidence remains in the existing `evidence_used` response.

- `backend/app/agent/providers.py`: cancellable async chat protocol, generation
  settings, safe provider errors, DeterministicProvider and OllamaProvider.
- `backend/app/agent/orchestration.py`: model loop, scoped schemas, controlled
  dispatcher, budgets, loop detection, extractive grounding and fallback.
- `backend/app/agent/contracts.py`: backward-compatible mode/response extensions;
  replaces the unused Step 1 `explain` placeholder with the chat provider boundary.
- `backend/app/routers/agent.py`: existing worker-thread read-only snapshot wraps
  orchestration; disconnect cancellation and per-statement database deadlines.
- `backend/tests/test_agent_orchestration.py`: mocked-model and real local PostgreSQL
  coverage; standard tests never require Ollama.
- `scripts/agent-ollama-smoke.py`: explicitly invoked live local model test.

The Step 1 tools, citations, deterministic answers, financial calculators,
authorization, transaction isolation and privacy projections are reused unchanged.
DeterministicProvider calls that baseline directly rather than imitating a neural
model or making an external request. The async ModelProvider protocol defines
`available(timeout)` and `chat(messages, tools, settings, timeout)`; coroutine
cancellation terminates pending HTTP work. Future hosted adapters can implement
this protocol and return ModelMessage. They must keep the same dispatcher and
validation, use secure backend-only credential configuration, and pass equivalent
wire/security tests. Hosted services remain optional and are not configured here.

## Model request/result flow

1. Authorize an active public project before model availability or generation.
2. Provide a system role, user question, and seven structured function definitions.
   Each schema pins project ID to the authorized project. The maintainer tool pins
   its identifier to that project's owner. Only paging tools accept an offset.
3. POST `/api/show` for the configured installed model; require `tools` capability.
   POST `/api/chat` with `model`, `messages`, `tools`, `stream:false`, `think:false`,
   `keep_alive:"5m"`, and `options` containing temperature 0, num_predict 512,
   num_ctx 8192. There are no pull/create/download calls.
4. Parse `message.tool_calls[].function.{name,arguments,index}`. Arguments must be
   a JSON object, not a JSON-encoded string. Validate names, types, exact scope,
   offset and extra properties before dispatch. Boolean IDs are rejected.
5. Execute existing read-only tools. Append the assistant tool-call message and
   one `{role:"tool",tool_name:name,content:serialized_public_envelope}` per call.
   Multiple tools and subsequent model turns are supported. Identical normalized
   name/arguments cannot repeat, even with changed wire indices or call IDs.
6. When the model returns final content, validate strict JSON selections, resolve
   them against evidence retrieved in this request, and render facts on the server.

Unknown tools, SQL, shell/Python/filesystem actions, arbitrary URLs and mutations
are never dispatched. The provider receives no Session or application object.
Its configured endpoint is operator-controlled, never supplied by a request or
model. Redirects, ambient HTTP proxy credentials and cookies are disabled for the
private Ollama connection. Keep it local or on an authenticated, restricted private
network; this adapter does not provision remote authentication.

## Grounding contract and limits

Rather than attempt an unreliable semantic verifier, this implementation deliberately
uses **extractive LLM answers**. The model selects relevant tools and scalar fields;
it does not write prose that the server presents as fact. Example final model JSON:

```json
{"facts":[{"reference":"<exact evidence.citation.reference>","pointer":"/financial_summary/net_recorded_funding_cents"}]}
```

Pointers address `evidence.value`; selected strings, booleans, numbers and dates are
rendered with the authoritative field path and citation. Objects, arrays, nulls,
unknown references, extra invented values, free-form conclusions and malformed
output are rejected. Financial currency is supplied from the backend summary.
No model arithmetic or model-generated labels enter the answer. All amounts,
statuses and dates displayed are exact backend projection values; backend finance
services still own refund/reversal exclusions and accounting. Citation references
must match full hashes from the current request, not a previous conversation.
Only selected envelopes/citations are returned; freshness, last-update information,
source limitations and public visibility are preserved. Quoted source descriptions
are explicitly untrusted reports, not independently verified claims.

**Citation existence does not establish semantic entailment.** Field selection can
be irrelevant, incomplete, cherry-picked, or misleading by omission. Free-form
summaries, causal explanations, aggregate computations, discrepancy adjudication,
and semantic truth of source text are deliberately outside this validator. The
fixed server disclaimer distinguishes reported spending, Sandbox records,
maintainer assertions and causes that records cannot establish. GitHub stale/unknown
freshness is included in both limitations and source_freshness. Nothing claims
fraud, honesty, settlement or why a delay happened.

If output cannot be validated, use the clearly labeled deterministic baseline when
still within budget. Novel questions outside that baseline may retain its
`unsupported_question` status. Exhausted time or failed DB reads produce explicit
insufficient evidence. An unavailable provider returns `provider_unavailable` in
LLM mode; auto may return a labeled deterministic fallback. Deterministic mode
works without checking Ollama. Always inspect actual execution_mode; requesting
LLM mode does not guarantee a grounded LLM response.

Public projections exclude private receipts, OCR, storage keys, backer identities,
auth tokens and unpublished expenses. Maintainer history intentionally includes
that owner's other **public active** projects; it never grants private access.
Source text may ask for tools, credentials or scope changes: it remains a tool-role
JSON value and has no authority over dispatcher restrictions. No source content or
chat is stored by this feature. Inherited public visibility changes still require
reauthorization before redisplaying cached answers.

## Configuration and execution bounds

All settings are backend environment variables; no frontend key is needed.

| Variable | Default | Allowed bound / meaning |
| --- | --- | --- |
| AGENT_MODE | deterministic | deterministic, llm, auto |
| OLLAMA_BASE_URL | http://localhost:11434 | Operator-configured origin only; no credentials/path/query |
| OLLAMA_MODEL | qwen3:4b | Candidate small model; see verification qualification below |
| AGENT_MAX_TOOL_CALLS | 6 | 1–6 successful calls |
| AGENT_MAX_TURNS | 3 | 1–6 generation calls; availability is separate |
| AGENT_TIMEOUT_SECONDS | 30 | >0–120, wall budget for orchestration |
| AGENT_MODEL_TIMEOUT | 15 | >0–60, each generation/availability request |
| AGENT_TOOL_TIMEOUT | 5 | >0–15, each tool plus PostgreSQL statement timeout |
| AGENT_MAX_CONTEXT_BYTES | 24000 | 4096–32000, serialized messages + definitions |
| AGENT_MAX_TOOL_BYTES | 12000 | 1024–24000, each model-bound evidence envelope |
| AGENT_MAX_RESPONSE_CHARS | 6000 | 500–8000, returned answer text |

Provider response bodies have a 32 KiB cap; parsed assistant content 8,000 characters,
six calls per message; final selections at most 12. The raw provider body limit also
bounds discarded thinking content. Context limits count UTF-8 serialized JSON bytes,
not exact model tokens. Ollama may still truncate a token context; missing citations
then fail validation. Answer text bounds do not cap the complete evidence response:
Step 1 evidence envelopes retain their separate 256 KiB ceiling. The existing
4 KiB streaming HTTP body cap, 20 requests/peer/minute, 120/process/minute, 2,048 peer
entries and four concurrent worker slots remain active, including during model waits.
Rate/concurrency limits return HTTP 429 with Retry-After, not a model error.

All DB work runs in the worker, not FastAPI's event loop, with REPEATABLE READ /
READ ONLY. Each SQL statement checks cancellation and remaining request time;
PostgreSQL statement_timeout bounds long-running statements. Cancellation closes
model HTTP work and releases admission only when the worker finishes. Disconnects
are checked every 250 ms. Deadlines are cooperative between Python operations;
these are not OS CPU/memory limits or protection against an unresponsive DB socket.
A timed-out SQL statement aborts the snapshot and produces insufficient evidence,
not a fallback on an aborted transaction.

A snapshot/connection can be held during inference for up to the configured budget.
Four GPU requests can queue or compete for KV cache; small CPU instances may routinely
hit the 15-second model deadline. Worker slots remain occupied during cancellation
cleanup. Existing materializing domain aggregations still require load testing.
Process-local quotas are neither distributed nor a substitute for trusted edge
limits, DB pool sizing, an authenticated model server, and process resource limits.

## Official sources and local Ollama verification

On 2026-11-03, the unversioned native API wire structures were checked against
[official API Go types](https://github.com/ollama/ollama/blob/main/api/types.go) and
[official Python tools example](https://github.com/ollama/ollama-python/blob/main/examples/tools.py).
MockTransport tests exercise POST show/chat, capabilities, function arguments,
assistant/tool role messages, non-streaming completion, errors and byte bounds.
No Ollama package version is pinned because HTTPX implements the native API.

The [official Qwen3 README](https://github.com/QwenLM/Qwen3) confirms released 4B
weights, tool support in thinking/non-thinking modes, Apache-2.0 open weights, and
Ollama usage (upstream recommends >=0.9.0). It also warns that Ollama tags may change.
**The current Ollama catalog/tag availability could not be verified:** this cloud's
network policy returned HTTP 403 for docs.ollama.com and ollama.com. Therefore
`qwen3:4b` is a configurable candidate, not a live-tested or catalog-certified tag.
The adapter verifies installed tool capability before use. No Ollama binary or GPU
is available here; no real inference, downloaded artifact, VRAM/latency benchmark,
model/server version or fresh external-model deployment is claimed.

For an approximately 8 GB VRAM development GPU, a quantized 4B model is a reasonable
candidate (roughly 2–3 GB weight storage at ~4 bits, plus runtime and KV cache).
This is an estimate, not measured peak memory; exact quantization, context,
concurrency and driver/runtime versions matter. Check the current official catalog,
license and installed model metadata first. Use a smaller context or lower
concurrency if memory is tight. The deterministic mode has no model memory cost.

On your own development machine, after independently installing a supported Ollama
release from its official source and verifying the tag in the current catalog:

```sh
# Explicit operator actions only, outside normal web requests:
ollama --version
ollama serve                   # keep on loopback; use an existing server if already running
ollama pull qwen3:4b           # only after verifying current tag/license; downloads weights
ollama show qwen3:4b
curl -s http://localhost:11434/api/show -d '{"model":"qwen3:4b"}'
# Confirm capabilities includes tools, inspect model details/quantization.
```

Ollama's own runtime may load a previously installed model on chat; web requests
never pull one. Localhost in Render/cloud refers to that server/container, not your
laptop. Do not open an unauthenticated Ollama port to the Internet. A local cloud
model needs separately provisioned capacity or a securely reachable private service.
Catalog/download hosts need explicit environment network access; this feature does
not broaden network policy or install a VPN/proxy bypass.

With an active synthetic project in a migrated local `opendev_test_*` database:

```sh
cd /workspace/OpenDev/backend
source /workspace/opendev-setup/local-env.sh  # or your own isolated local configuration
export OLLAMA_BASE_URL=http://localhost:11434 OLLAMA_MODEL=qwen3:4b
python ../scripts/agent-ollama-smoke.py --project-id 42
```

Replace 42 with the actual active project ID. The script refuses production/remote
DB targets, prints actual Ollama version and safe diagnostics, and fails unless a
validated LLM answer with citations results. It does not run automatically in pytest
or CI. Verify facts against the cited API projection, and test a natural multi-source
question as well. First-run model latency may need deliberate timeout tuning.

## Validation and remaining gates

Standard commands from backend/ with isolated DATABASE_URL and TEST_DATABASE_URL:
`python -m pytest -q`, `python -m alembic upgrade head`, `python -m alembic check`.
From frontend/: `npm test`, `npx tsc -b`, `npm run build`, `npm run lint`.
No schema migration was needed; head stays `8c6072dabc59`.

Tests cover single/multiple/multi-turn calls, actual current-request citations,
forged references and values, causal/date fabrication rejection, unknown/malformed
arguments, cross-project and unrelated-maintainer denial, public privacy projections,
hostile GitHub text, duplicate loops including changed indices, provider/model/SQL
timeouts, unavailable/auto/deterministic behavior, simultaneous API queries,
context/call/turn/response bounds, cancellation, immutable financial records and
old-client bodies. Existing foundation tests additionally check all seven tools,
read-only SQL rejection and financial invariance. HTTP/provider responses are mocked;
PostgreSQL and the existing projections are real in integration tests.

Live model quality, catalog availability, GPU capacity, authenticated private
connectivity, multilingual/complex-question relevance, load testing and adversarial
model evaluation remain unverified. Extractive answers intentionally trade prose
quality for verifiable values; a richer explanation needs a separately reviewed
claim/entailment policy. All previous licensing, credential-history, private storage,
Sandbox, HTTPS/cookie and hosting gates remain open. **Deployment stays NO-GO.**

Final local validation on 2026-11-03:

- **307 backend tests passed, none failed/skipped** (278 baseline + 29 new cases),
  128.31 seconds against isolated PostgreSQL. Concurrent requests and SQL timeout
  tests also passed. Additional direct check verified answer-length rejection.
- **26 frontend tests passed**, TypeScript check, production build and lint passed.
- Alembic upgrade/check passed with no schema drift; Python compilation,
  smoke-script `--help`, and `git diff --check` passed.
- Existing Starlette HTTPX deprecation, two AuthContext lint warnings and large Gantt
  chunk warning remain. No live Ollama inference or GPU benchmark was run.
