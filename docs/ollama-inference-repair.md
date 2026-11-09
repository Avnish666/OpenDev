# Ollama inference validation repair

The reported response (`deterministic`, no successful tools, turn 1, generic
validation fallback) locates the failure before a successful tool result, but does
not identify whether it was a model deadline, missing native tool call, or invalid
arguments. The old catch-all deliberately discarded that distinction. Latency
alone does not prove a timeout. `think: false` was already present.

A code defect was reproduced with synthetic model replies: a first native-tool
turn containing prose or JSON without `message.tool_calls` was immediately passed
to the final evidence validator with an empty evidence set. It fell back without
attempting tool selection again. The provider also supplied no Ollama `format`
schema for the strictly validated final JSON, and did not classify token-limit
truncation. This is a reproduced failure mechanism, not proof of which output the
user's original Ollama daemon emitted.

## Changes

- Separate the initial, concise native-tool-selection instruction from answer
  selection. Include the server-authorized integer project and owner IDs.
- Retry missing first-turn native calls once, within the existing total time,
  turn, context and tool limits. Discard the unvalidated response; never echo it.
- After evidence retrieval, use Ollama's root-level `format` JSON schema with no
  simultaneous native `tools` decoder. Restrict references to evidence retrieved
  in the current authorized request. A structured `tool_requests` branch permits
  further evidence retrieval through the same strict dispatch checks.
- Keep `think: false`, temperature zero, bounded nonstreaming responses, disabled
  ambient proxy/redirects, and all existing authorization, read-only snapshots,
  exact financial/citation checks and server-rendered answers.
- Detect `done_reason: length` before interpreting partial output. Preserve honest
  deterministic fallback; never label a fallback as LLM execution.

## Development diagnostics

Only `APP_ENV=development` adds `diagnostics.llm_failures` and emits metadata to
logger `app.agent.diagnostics` at INFO level. Other environments retain only the
existing tool-name, turn-count and latency diagnostics. No exception strings,
tracebacks, prompts, model text, arguments, project IDs, URLs, secrets, or evidence
are recorded in the additional metadata.

Examples of finite, allowlisted codes:

| Stage | Category | Meaning |
| --- | --- | --- |
| `tool_selection` | `missing_tool_calls` | Native response did not select a tool; one retry is permitted. |
| `tool_validation` | `invalid_tool_arguments` | Argument types, fields, identifier, or offset failed validation. |
| `tool_validation` | `unknown_tool` | Function was outside the public tool allowlist. |
| `model_request` | `model_timeout` | Orchestration model-call deadline expired. |
| `model_request` | `provider_timeout` | Provider transport/read deadline expired. |
| `model_request` | `model_output_truncated` | Ollama reported a token-limited generation. |
| `answer_validation` | `malformed_structured_output` | Final content was not JSON. |
| `answer_validation` | `invalid_answer_schema` | Final JSON violated the allowed structure. |
| `answer_validation` | `invalid_citation_or_fact` | Citation, pointer, source combination, or financial claim failed validation. |

Recovered missing-call attempts remain visible in the metadata. An answer is LLM
only after subsequent retrieval and final validation succeed; the presence of a
recovered diagnostic does not mean deterministic fallback occurred.

## Verification and real-model acceptance

Tests use real isolated PostgreSQL projections and simulated Ollama responses.
The API acceptance regression asks exactly “How much funding has this project
received?” and requires `llm`, `answered`, successful `get_project_finances`, a
matching financial citation, the known synthetic funding amount, and no fallback.
The suite also covers a missing native call followed by recovery, invalid scope
and argument types, additional structured tool requests, malformed final output,
fabricated citations, timeouts, truncation, diagnostics privacy and production
suppression. Existing financial, development, authorization, cancellation and
capacity regressions are retained.

In this cloud workspace the actual metadata probe found no Ollama executable or
listener at `127.0.0.1:11434`. Real Qwen3 inference could not be run. No model or
runtime was installed or downloaded, and simulated provider success is not live
inference acceptance.

To run the opt-in real-model regression on a machine with an already installed
local `qwen3:4b`, use an isolated loopback PostgreSQL database named
`opendev_test_*` (never production):

```sh
cd backend
# Set DATABASE_URL and TEST_DATABASE_URL to that same disposable local database.
APP_ENV=testing LLM_ENABLED=true OPENDEV_TEST_LOCAL_OLLAMA=1 \
  OLLAMA_BASE_URL=http://127.0.0.1:11434 OLLAMA_MODEL=qwen3:4b \
  python -m pytest -q -s tests/test_agent_ollama_pipeline.py \
  -k actual_local_ollama_funding_acceptance
```

The existing fixture migrates a new isolated schema, creates a synthetic public
project/contribution, and drops that schema afterward. The opt-in test validates
local model availability first, then uses the real provider and original evidence
validators. It fails if inference falls back or omits financial evidence. The
normal suite skips this test unless explicitly enabled. Its generous 120-second
request / 60-second per-model test bounds do not change application defaults.

For diagnosis in the actual development app, restart the backend with
`APP_ENV=development`, repeat the funding question, and inspect only
`diagnostics.llm_failures`. This reveals the actual category of a remaining local
failure without collecting raw model output.
