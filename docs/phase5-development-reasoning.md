# Phase 5 Step 4: development and maintainer reasoning

**Deployment remains NO-GO.** This extends the existing single read-only agent.
No paid API, model download, write tool, new table, migration, trust score,
automatic delivery certification, frontend conversation UI, commit or push is added.

## Files and architecture

- New `backend/app/agent/development_reasoning.py`: typed claim plans, deterministic
  UTC deadline analysis, explanation templates and explicit intent aliases.
- Modified `backend/app/agent/tools.py`: existing roadmap evidence gains page-scoped
  counts, owner ID, evaluation timestamp and per-commitment deadline analysis;
  GitHub evidence gains evaluation-time freshness. Existing public schemas, paths,
  citations, history and source services are reused.
- Modified `backend/app/agent/answers.py`: deterministic development and cross-domain
  intents; existing financial and other baseline intents remain supported.
- Modified `backend/app/agent/orchestration.py`: prompts and grounded claim-plan
  dispatch; provider adapters, cancellation, admission and resource limits unchanged.
- New `backend/tests/data/development_agent_evaluation.json` and
  `backend/tests/test_agent_development.py`: reproducible evaluations and security/
  contract regressions. This document records design and validation.

No new tool is needed: get_project_roadmap, get_github_activity,
get_maintainer_history, get_reward_fulfillment and get_project_finances already
cover authorized public sources. The seven-tool allowlist and project/owner pins
remain unchanged. Roadmap projections reuse `credibility.delivery_rows`,
`progress.counts`, public `roadmap.view/history`, and immutable history. Financial
claims reuse Step 3 templates and existing accountability calculations, never model
arithmetic. Source financial, payment, reward and milestone services are unchanged.

## Evaluation and deadline rules

`EvidenceTools(reader, evaluation_at=<aware datetime>)` is the internal reproducible
entry point. Omission uses the transaction timestamp. Naive timestamps are rejected;
aware timestamps are normalized to UTC. Public API bodies do not accept a model-
chosen evaluation date. Citation retrieval time stays separate from evaluation time.

For each retrieved roadmap commitment:

- Original deadline and actual asserted delivery date use the existing immutable
  history reconciliation, including matching the current stored assertion.
- Current deadline is the current planned end date.
- Current/original overdue days are max(0, UTC evaluation date − deadline) for
  unfinished statuses; delivered and cancelled commitments are excluded.
- Late days are actual asserted delivery date − original deadline when classified
  late. On-time is zero. Missing original/matching delivery dates remain unknown.
- Deadline revision count walks the full bounded ordered immutable history and
  counts changes of recorded planned_end_date after its first occurrence. Reordering,
  evidence and status-only events do not increase that count.
- Reopened, cancelled and submitted-for-review states retain the existing service
  classifications. Rescheduling never substitutes a revised date for the original
  commitment in on-time/late analysis.

Roadmap counts and lists cover **one 50-record page**, not the full project. Models
can retrieve bounded additional offsets; each claim must name its own page citation.
History display previews remain at most 50 events/milestone. Revision calculations
use all history for the page within a 10,000-event cap; larger scopes are rejected.
A missing original deadline makes timing explanations insufficient evidence, rather
than pretending the current date is original. The original creation record may
predate publication; first-publication deadlines were not separately persisted.

An earlier evaluation timestamp applies date arithmetic to current records; it is
**not a historical state replay**. Later statuses/edits are not reconstructed as of
that time. This caveat is included in answers. GitHub freshness similarly evaluates
available sync metadata, not a historical repository archive; snapshots postdating
an evaluation cannot establish freshness at that earlier time.

## GitHub observations and limitations

Counts for open/closed issues and open/closed/merged PRs come from existing retained
snapshots. Closed PR counts overlap merged PR counts and are never added as disjoint
buckets. GitHub milestone lists and recent commits are explicitly page/sample data.
Linked issue/PR/milestone/commit evidence comes from authorized public roadmap links,
with stable IDs, existing safe URLs, availability, merge/state and stale flags.
Known private/unavailable sources retain their existing withholding behavior.

Last success, current latest attempt, snapshot observation and evaluation times are
distinct. The evaluation-time freshness field uses the six-hour policy, recorded
latest failure and last-success time. No live GitHub request is made by the agent.
Collections can be bounded, commits sampled, deleted records retained, and activity
unlinked to funded work. A closed issue or merged PR **never changes delivery**.
Support answers identify links but explicitly cannot certify deliverable completion.

No complete comparable activity windows are available. Activity-trend answers are
insufficient evidence. Missing recent observations do not establish abandonment.
Cross-domain spending trends and activity-after-funding chronology are also
insufficient: aggregate financial tools do not expose immutable financial windows
or per-capture funding dates. The agent does not fabricate increases, percentages,
causal explanations, dishonesty allegations or funding-misuse claims.

## Maintainer indicators

Public profiles are restricted to currently owned **active** public projects.
Owner delivery outcomes, participation, rewards, financial reporting and repository
signals remain separate in the returned evidence. Collaborators/maintainers do not
inherit every team outcome. Current ownership is not historical ownership.

Delivery counts/ratios reuse existing numerator, denominator, sample size, state and
formula fields. Empty delivery history is **Insufficient history**, never zero
trust. Reward fractions are exact eligible fulfilled/eligible entitlement counts;
completed matching-currency captures only, excluding refunded/reversed contributions
and revoked/invalid entitlements. Fulfillment is a maintainer mark, not independent
proof. No reward deadlines or status-change timestamps exist for overdue/chronology.

The current project/owner comparison shows page counts beside the owner's aggregate.
That aggregate includes the current project; it is not an independent previous-
outcome cohort. Non-active projects are excluded, so no lifetime/past-project count
or previous ownership is invented. Financial amounts remain per project/currency;
GitHub team activity is not personal authorship. There is no composite rating.

## Claim validation and API compatibility

The same POST `/api/projects/{id}/agent/query` and AgentAnswer schema apply in
`deterministic`, `llm` and `auto` modes. Deterministic aliases cover the documented
questions in `development_reasoning.INTENTS`, as well as the existing overdue
question. Existing financial and legacy clients remain supported.

The model may select exactly one final output format: scalar facts, financial_claims,
or development_claims. Example development plan:

```json
{"development_claims":[{"kind":"funding_schedule","references":["<roadmap reference>","<finance reference>"]}]}
```

Kinds include progress, overdue, on_time, deadlines, roadmap_changes, github_activity,
linked_evidence, activity_trend, delivery_support, schedule_explanation,
missing_delivery_evidence, maintainer_history, reward_history, owner_comparison,
funding_schedule, spending_trend and after_funding. Required source domains are
validated per kind; owner comparison additionally verifies owner identity. Unknown,
foreign, nonpublic or unrelated citations cannot support a claim. Model-provided
counts, dates, statuses, URLs, causal text and other extra fields are rejected.

The server supplies values, relationships, citations and limitations. References
must match evidence retrieved in this request, including projection hashes and
source paths. Public schema boundaries suppress draft projects, originals, private
OCR/reviews, backer notes/tokens and private collaborator data. Retrieved text is
untrusted data and cannot alter dispatch permissions. Oversized answers or uncertain
model output use the existing bounded deterministic fallback/insufficient response;
execution_mode reports actual use. No prompts or source text are persisted by default.

Citation presence does not prove relevance, completeness, source truth or semantic
entailment. Templates constrain supported relationships but cannot independently
verify a maintainer assertion, infer motivations, certify delivery, or adjudicate
honesty. The statements and indicator calculations are evidence descriptions, not
a calibrated assessment of a person.

## Evaluation and manual checks

The JSON dataset contains **30 scenarios**, each with expected facts, citation kinds,
forbidden claims, limitations and answer status. It covers on-time/late/overdue,
revisions/multiple revisions, reopened/cancelled/submitted states, merged versus
unmerged PRs, closed issues, links/missing evidence, stale/failed sync, sampled
commits, absent original deadline, insufficient history, collaborator attribution,
reward eligibility/revocation, multiple active projects, funding/schedule,
causal/allegation constraints, roadmap changes, unavailable trends/chronology and
hostile source text. Additional tests cover invented counts/dates/statuses/URLs,
unknown/foreign citations, draft privacy, mocked multi-turn cross-domain reasoning,
deterministic fallback, UTC offset equivalence, naive-time rejection and API schema
compatibility. Financial evaluation scenarios are retained unchanged.

Only local isolated PostgreSQL and mocked providers are used. **Live Ollama was not
run**; previous catalog-access, GPU, memory and model-quality limitations remain.
No new inference-performance claim is made. Source counts/history are bounded and
materialized; large pages/profiles may exceed existing tool/context/answer limits.
Process-local quotas, DB pool/host capacity, source authenticity and broader
adversarial model testing remain release concerns. All inherited deployment gates
remain open.

From backend/ with an isolated local opendev_test_* database:

```sh
source /workspace/opendev-setup/local-env.sh
APP_ENV=testing python -m pytest tests/test_agent_development.py -q
APP_ENV=testing python -m pytest -q
python -m alembic upgrade head
python -m alembic check
```

From frontend/: `npm test`, `npx tsc -b`, `npm run build`, `npm run lint`.
Against an active synthetic project, POST a normal query body with question
“What progress has this project made?” or “How much funding has this project received,
and which commitments are overdue?”; compare citations to public roadmap/history,
GitHub activity, transparency and owner credibility endpoints. Check missing-original,
reopened and changed-deadline cases; inspect stale/source notes and page boundaries.
Use the internal aware evaluation timestamp for fixed date tests. Never use Neon or
production financial data for fixtures.

After explicitly provisioning local Ollama as described in Step 2, optionally run
`python ../scripts/agent-ollama-smoke.py --project-id <synthetic-id> --question
'How much funding has this project received, and which commitments are overdue?'`.
Require actual llm mode and inspect both citations; fallback is not live-inference
proof. Do not expose an unauthenticated model server publicly. **NO-GO remains.**

Roadmap citations fingerprint the public bundle (commitment, delivery projection,
history preview and derived analysis), not just one GET response. Derived fields
are reproduced by these backend tools with the same current records/evaluation time;
there is no immutable archived answer store. Reauthorize public visibility before
redisplaying old evidence and do not treat a later digest as the same snapshot.

## Recorded validation

2026-11-03 local verification:

- **380 backend tests passed, 0 failed/skipped**, 194.81 seconds. This includes
  the 342 preceding cases and 38 development cases. The final dataset/invariance
  run also passed 38/38, including **30/30 evaluation scenarios**; the unchanged
  15 financial scenarios remain covered by the complete suite.
- **26 frontend tests passed**. TypeScript, production build and lint passed;
  existing two AuthContext warnings and the large lazy Gantt chunk warning remain.
- Local Alembic upgrade/check passed without schema drift; migration head remains
  `8c6072dabc59`. Compilation, whitespace and generated API schema compatibility
  checks passed. AgentQuestion fields and AgentAnswer fields remain compatible.
- The first complete run exposed a fixture whose synchronization timestamp was
  later than its fixed evaluation instant. Correctly unknown freshness was initially
  expected to be stale. Fixed synchronization metadata now precedes evaluation;
  the scenario and final complete suite pass without weakening the freshness rule.
- Existing Starlette/HTTPX TestClient deprecation remains. Live Ollama, external
  acceptance, hosted CI, production migrations and deployment were not run.
