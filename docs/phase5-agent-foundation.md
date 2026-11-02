# Phase 5 Step 1: public evidence foundation

Deployment remains **NO-GO**. All Phase 3/4 licensing, historical credential review,
private storage/live Sandbox, hostile document handling, HTTPS cookie/domain and
free-host capacity gates remain open. No model service, paid API, database migration,
production connection, commit, push or deployment is introduced by this step.

## Architecture and changed files

Existing FastAPI modular monolith, extended with `app/agent/`:

- `contracts.py`: AgentQuestion, AgentEvidence, Citation, AgentAnswer, typed ToolCall
  allowlist and optional ModelProvider protocol.
- `tools.py`: typed public retrieval functions and bounded allowlisted dispatch.
- `citations.py`: normalization through public schemas, canonical JSON SHA-256 and
  stable source/citation identifiers. No URLs are fetched or invented.
- `answers.py`: deterministic intent routing and factual template responses.
- `limits.py`: bounded local admission/rate/concurrency controls.
- `routers/agent.py`: bounded request parsing and read-only transaction execution;
  registered in `app/main.py`.
- `services/credibility.py`: existing reward eligibility/formulas extracted into
  `reward_statistics`, shared by unchanged profile calculations and project tools.
- `tests/test_agent.py`: retrieval, privacy, citation, baseline and read-only tests.

No frontend changes, new dependency, vector store, Redis/Kafka, microservice, AI
reasoning engine or write tool. Tool code exposes only domain projections; future
providers must receive serialized public evidence, never ORM sessions or secrets.

## Retrieval tools

Every project tool independently calls the existing active-public-project check.
They ignore session privileges; an owner cannot use them to see their own drafts.
The constructor rejects writable database transactions. API execution uses existing
`accountability.read_snapshot` (PostgreSQL REPEATABLE READ / READ ONLY), so accidental
SQL mutations are rejected by PostgreSQL, not just a prompt instruction.

| Python tool | Authoritative source and output |
| --- | --- |
| `get_project_overview(project_id)` | Public ProjectResponse: project/status/repository ID/link, goal and currency |
| `get_project_finances(project_id)` | Anonymous `transparency.overview`, PublicTransparency schema: captured gross, refund/reversal exclusions, net, published reported spending, category variance, coverage and existing notes |
| `get_project_expenses(project_id, offset=0)` | Public ledger: 50 published reports/page, approved-redaction metadata and public category discrepancies |
| `get_project_roadmap(project_id, offset=0)` | Public roadmap views, shared `credibility.delivery_rows` original/current deadlines, assertions and up to 50 public immutable history events per milestone |
| `get_github_activity(project_id, offset=0)` | Public activity/milestone schemas, canonical GitHub IDs and SHA sample, last success and stale flags; known unavailable/private source denied |
| `get_maintainer_history(maintainer_id)` | Existing public credibility profile: current owned active projects, timing/reopens/cancellation, rewards, per-project reporting and insufficient-history states |
| `get_reward_fulfillment(project_id)` | Same reward statistics helper, scoped to just that active project; no backer identities or fulfillment notes |

Pages include scope/limits/offset where applicable. Roadmap retains stable IDs and
versions, plus immutable history UUIDs and original deadlines even if history preview
is truncated. GitHub canonical repository ID identifies the evidence envelope;
individual issue/PR/milestone IDs and full commit SHAs identify nested records.
GitHub source coverage is bounded and retained; a fresh sync is not exhaustive.
No live provider/network/storage operation is performed by retrieval.

Offsets are bounded 0..10,000. Maintainer profiles above 20 active owned projects or
10,000 owned milestone history events are rejected as outside baseline capacity.
Normalized tool payloads above 256 KiB are rejected, not silently shortened. Existing
aggregations still materialize records before this size check; these are not hard
process memory/time limits. Per-project accounting and large histories remain
scaling limits noted in Phase 4; deployment ingress/resource validation remains open.

## Contracts and citations

`AgentQuestion`: strict positive project_id, trimmed 3..1,000 character question,
extra fields forbidden. Both the body ID and path ID must match.

`AgentEvidence`: source_type, stable source_id, project_id (null for user-wide history),
claim, JSON value, observed_at (retrieval transaction time), last_updated_at when
known, public visibility classification, freshness, citation, limitations. Public
schema validation removes unspecified ORM fields before normalization.

`Citation`: source_id, reference, real source API path, method (GET by default),
optional request_body for POST-only project reward queries, full projection_sha256,
and retrieved_at. Example reference shape:
`opendev:project:42:overview@sha256:<full-64-character-digest>`.
The ID is stable; digest identifies the exact returned canonical JSON payload.
A future retrieval may differ, including calculation timestamps. This is not an
immutable archive or proof the old payload remains publicly available. Keep returned
payload/hash with an answer, reauthorize before re-displaying it, and signal a digest
mismatch rather than silently equate old and new evidence. Historical event UUIDs
remain stable; public scope can shrink when a project becomes non-active.

Aggregate citations link to existing source endpoints. Roadmap/GitHub bundles contain
additional related sources, with their stable IDs and explicit history/milestone
retrieval paths in limitations. They are bundle fingerprints, not provider signatures
or a claim that one GET yields byte-identical data. Project reward citations use the
real POST query endpoint with `{project_id, question: "reward_fulfillment"}`.
No signed document bearer URLs, storage keys, original receipt IDs or private OCR
are included. Only approved redaction IDs already authorized by the ledger appear.

Freshness classifications are `current_database_snapshot`, `stale`, `unknown`.
A current database read does not establish live settlement, GitHub completeness or
independent verification. Unknown financial/reward source-change time remains null;
retrieval/calculation time is kept separate. Supporting receipts never verify payment.

## Deterministic API

`POST /api/projects/{id}/agent/query`, JSON body, public active projects only:

```json
{"project_id": 42, "question": "How much funding has the project received?"}
```

Supported exact intents (or the documented question text in `answers.INTENTS`):
`funding`, `spending`, `categories`, `overdue`, `delivered`, `github_sync`,
`maintainer_history`, `reward_fulfillment`. Case, trailing question marks and repeated
whitespace are normalized. No semantic matching, hidden model fallback or arbitrary
SQL/URL/command execution. Source text is data even if it resembles instructions.

Answers contain answer text, citations, evidence_used, limitations, confidence
classification and answer_status. Confidence is categorical, never a calibrated
number or trust score. Status is `answered`, `insufficient_evidence`,
`unsupported_question`, or `unavailable_source`. Empty delivery history is insufficient,
missing/hidden GitHub and oversized source scopes are unavailable. Draft or missing
project lookup returns 404 even for unsupported questions. Zero recorded funding is
an explicit database observation, not a claim no external funding exists.

All amounts use integer minor units with currency and existing accounting rules.
Refund/reversal-affected captures remain conservatively excluded in full; exact
partial refunds remain unknown. Delivery/fulfillment remain maintainer assertions.
Overdue includes unfinished planned/in-progress/submitted commitments before today
UTC, excluding delivered/cancelled. Baseline overdue/delivered answers disclose first-
page scope; evidence tools support paging, but the baseline does not infer beyond
retrieved records. No numerical reputation or personal honesty inference.

## Request, privacy and abuse controls

Request bytes are streamed with a 4,096-byte cap before JSON parsing (413), JSON
content type required (415), malformed/schema/ID mismatch 422. Validation errors do
not echo raw prompts. Nothing persists questions, answers or source text by default.
API-wide no-store/no-referrer/nosniff headers apply. This POST is a public read and
has no authenticated state-changing behavior; existing write CSRF policy is unchanged.
No private retrieval mode is exposed, even with a maintainer session.

Admission uses remote socket peer, ignoring spoofable forwarding headers: 20 queries
per peer per 60 seconds, 120 globally per process, at most 2,048 tracked peers and
four concurrent database readers. Limits return 429 with Retry-After. Rate state is
memory-only, resets on restart and is not shared across workers. A proxy may group
many legitimate visitors under one peer; configure a separately verified trusted edge
policy before deployment rather than trusting arbitrary X-Forwarded-For headers.
Ingress body/time quotas and distributed limits remain deployment requirements.
These controls do not resolve inherited release blockers.

## Step 2 interface

A future optional provider implements `ModelProvider.explain(question, evidence)`.
There is no mandatory provider/key/dependency. Typed ToolCall allows only seven names,
a strict numeric identifier and bounded offset; `invoke` checks the allowlist before
attribute lookup. Provider text cannot select arbitrary SQL or URL paths.

The application must authorize each tool invocation within a fresh read-only snapshot,
validate all tool inputs, enforce call/token/time/output budgets and supply only
public envelopes. Treat questions, GitHub text, expense text and public reasons as
untrusted quoted data. Validate model citations against evidence actually returned;
reject invented references or uncited claims and keep uncertainty explicit. Do not
hand a provider a Session, network client, filesystem interface or unrestricted tool
object. This protocol itself does not enforce future provider behavior: Step 2 must
implement/test the orchestrator. No model-generated action may write payment,
expense, review, publication, reward or delivery records. Human work uses existing
protected interfaces separately.

## Validation and manual checks

Final verification:

- **278 backend tests passed, 0 failed/skipped** (257 preceding + 21 foundation
  cases), 148.06 seconds on disposable local PostgreSQL.
- **26 frontend tests passed, 0 failed/skipped**. TypeScript, production build and
  Oxlint passed. Frontend code and dependencies were unchanged.
- Fresh Alembic upgrade and `alembic check` passed with no model drift; no historical
  migration was modified. Python compilation and `git diff --check` passed.
- Generated OpenAPI request/response contract checked, including the 1,000-character
  question bound. Streaming parsing remains manual so body limits precede decoding.

Coverage includes all seven tools, amounts/refund exclusions and citations,
private expense/original/OCR exclusion, original deadlines, GitHub freshness and
missing sources, no-history states, project reward isolation, active-only access
regardless of login, content-hash changes after updates, prompt-like source text,
malformed/oversized/extra-field questions, rate/concurrency limits, tool input and
payload bounds, and PostgreSQL read-only write rejection/financial invariance.
The shared credibility suite verifies the reward-helper extraction preserves behavior.

Existing Starlette TestClient warning, large lazy Gantt build warning and two
AuthContext lint warnings remain. No live-service, browser run for a new agent UI
(none was requested), or hosted CI claim is made.

Use the existing disposable local PostgreSQL instructions (database name
`opendev_test_*`, never Neon), then from backend/:

```sh
python -m alembic upgrade head
python -m alembic check
python -m pytest -q
```

From frontend/: `npm test`, `npx tsc -b`, `npm run build`, `npm run lint`.
No new migration is necessary; head remains 8c6072dabc59.

On a local API with an active test project:

```sh
curl -H 'Content-Type: application/json' -d '{"project_id":42,"question":"funding"}' http://localhost:8000/api/projects/42/agent/query
```

Replace 42 with a real local synthetic project ID. Check minor-unit amounts against
`/transparency`, compare category totals, inspect citation hashes/paths, then query
all supported intents. Verify empty history, stale/absent GitHub, draft 404, extra
fields/mismatched IDs, >4 KiB body rejection and 21st rapid query returning 429.
Compare anonymous and owner results: neither exposes private drafts/receipts/OCR/
notes/backer data. Change a public record, verify stable source ID with new digest,
and recheck active visibility. Inspect PostgreSQL records before/after: no mutation.
Do not use production credentials for these checks.
