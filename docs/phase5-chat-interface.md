# Phase 5 Step 5: public accountability chat

**Deployment remains NO-GO.** No second agent, financial calculation, paid service,
streaming protocol, persistence, database change, payment/expense logic, commit,
push or deployment is introduced. Pending Step 4 changes are preserved.

## Files and component architecture

- `frontend/src/api/agent.ts`: TypeScript contracts matching actual AgentQuestion,
  AgentAnswer, AgentEvidence and Citation; runtime shape validation, bounded question
  input, AbortSignal support, safe HTTP errors/Retry-After, public source mapping.
- `frontend/src/components/ProjectAIChat.tsx`: reusable public component, bounded
  exchange history, composer, mode control, AgentResponse and CitationList.
- `frontend/src/components/ProjectAIChat.css`: responsive layout and evidence styles
  based on existing OpenDev colors, typography, buttons and focus conventions.
- `frontend/src/pages/Projects.tsx`: active projects offer an on-demand chat panel;
  lazy import under Suspense keeps it out of the initial dashboard bundle.
- `frontend/tests/agent-fixture.mjs`, `agent.test.mjs`: mocked API/SSR contract,
  safety and error tests, without authentication or a running model.
- `frontend/tests/browser-chat-smoke.mjs`: explicit Chromium/CDP interaction smoke
  with a local mock API. This document records behavior and verification.

No new dependency or lockfile change is needed. The chat mounts only for active
public project details. Owner ID is supplied from the existing public ProjectDetail,
not chosen by a model. Its session is keyed by project ID, so navigation aborts
pending work and resets that project's transcript. There is no duplicate ledger,
roadmap, Gantt, auth context or agent implementation.

## Request/response mapping

POST `/api/projects/{projectId}/agent/query` sends only:
`{project_id, question, mode}`. Question is trimmed and restricted to 3–1,000
characters; existing backend validation/body/admission quotas remain authoritative.
The existing configured VITE_API_URL origin is reused, with credentials included,
JSON content type and no-store. This read-only public endpoint requires no sign-in.

Response handling uses answer, citations, evidence_used, limitations, confidence,
answer_status, execution_mode, source_freshness and diagnostics as actually defined
by the backend. Unknown modes/statuses or malformed/private evidence envelopes are
rejected rather than displayed as successful answers. Provider diagnostics, raw
JSON values, internal prompts and unrestricted evidence are not dumped into the UI.
No monetary arithmetic or new percentages are calculated by React; answer text
retains the backend's exact integer wording, even beyond JavaScript's safe integers.

HTTP 400/422, 401/403, 404, 429, 408/504, 503 and other failures have safe fixed
messages; backend traces/error bodies are not echoed. Numeric or HTTP-date
Retry-After is honored for up to an hour by a manual retry cooldown, retained across
Clear conversation. No automatic retry loops. A 403/404 query discards older answers
in the panel rather than continuing to display answers for a now-denied project.
Other errors retain preceding exchanges and offer manual retry of the same independent
question. Network failures, malformed JSON, response-shape failures, browser timeout
and user cancellation are distinct. The browser deadline is 45 seconds; this can be
shorter than a separately configured server maximum.

Mode choices: Deterministic uses backend rules; LLM requests model-assisted tool
selection and requires an available provider; Auto permits deterministic fallback.
No capability/configuration endpoint exists, so the conservative UI default is
Deterministic, independent of any hidden backend default. The backend is always
sent the user's explicit selection. The displayed **returned** mode comes from
execution_mode, not the request. Auto fallback therefore says Deterministic. A
provider_unavailable response is explicitly labeled unavailable and does not claim
a live model answered. Live Ollama availability is not promised or discovered here.

## Conversation, request races and cancellation

React state holds at most 12 exchanges (24 user/assistant bubbles), with stable
monotonic keys. There is no localStorage, sessionStorage, PostgreSQL or analytics
transcript. Refresh, project change and unmount clear this state. Earlier messages
are **never sent**; each query is independent, including retries. The UI says this
explicitly and suggestions use phrases actually supported by backend intents.

A synchronous AbortController ref prevents duplicate requests, including submissions
before React has rerendered. Each completion must still own the active controller
before updating state. Cancel, clear, timeout and unmount abort the browser request;
clear/navigation prevent late responses from repopulating the transcript. Input,
error and loading states are controlled independently. Requests are non-streaming:
loading text describes retrieval, not simulated tokens.

Browser cancellation does **not** guarantee immediate model/process cancellation.
The existing backend implements cooperative disconnect/deadline handling; GPU work
or cleanup may still run. Cancellation messages explain this. A client-aborted POST
is not an instruction to mutate or roll back financial records (the query is read-only).

## Citation-link safety

CitationList shows human-readable domain titles, fixed evidence explanations,
classification, retrieved/source-update times, freshness and expandable exact
references/projection hashes. Unknown timestamps remain unknown. “Current database
snapshot” is explicitly not live independent verification. Stale answers also get a
visible warning before opening citation details. No citations is explicitly disclosed.

A supported citation must match its current answer's evidence reference/source ID
and full 64-character lowercase hash. Known identifiers map to explicit public API
routes for this project: overview, transparency, ledger page, roadmap page, GitHub
activity page. Maintainer credibility is allowed only for the supplied public owner.
The backend api_path must match the reconstructed known route exactly. Cross-project,
absolute, protocol-relative, javascript/data, document/download and unknown paths
have **no link**. No arbitrary model URL or text is interpreted as navigation.
The only API origin is trusted VITE_API_URL; non-HTTP(S) or credential-bearing
configured URLs do not become citation links. Model-provided external hosts are
never linked, including arbitrary GitHub links: the public GitHub API projection is
the citation destination instead. New tabs use noopener/noreferrer.

Reward citations require a read-only POST and therefore remain non-clickable with
an explanation; the frontend never executes a citation's request_body. There are no
private receipt, signed URL, OCR, storage-key, reviewer-note or raw evidence viewers.
Unrecognized source identifiers are withheld; unknown sources show fixed metadata
and “No safe public link”. No original document can be opened through chat.

Opening a known public source requests its **current** API projection, which
reauthorizes visibility and may return 404 or changed data. The hash fingerprints
retrieved evidence, not an immutable archive, provider signature, independent audit
or proof of semantic entailment. The browser does not recompute hashes of parsed
financial JSON (unsafe integer rounding would make that misleading). Server-side
claim validation remains authoritative. A future full verification workflow must
compare original canonical projections and handle revoked scope explicitly.

Answer text, user text and limitations are React text nodes with preserved newlines;
no HTML/Markdown parser, dangerouslySetInnerHTML, auto-linker or token animation is
used. Hostile source/model strings cannot create markup or links. Backend public
projections remain the primary privacy boundary; the client cannot identify a secret
mistakenly embedded in otherwise valid answer prose. Review publication policy and
backend projections as part of the unchanged deployment gates.

## Accessibility, layout and performance

The composer has an explicit label/help, character count, auto-resizing textarea,
Enter submit, Shift+Enter newline and IME composition protection. Suggestions fill
and focus the input rather than silently submitting. Submit is disabled when invalid,
busy or rate-limited. Cancel and Clear use normal buttons; loading and cancellation
are announced via a concise polite status region. Errors use alerts, history has
aria-busy, and completed answers receive heading focus. Native details/summary
provide keyboard-operable citation/limitation disclosure without announcing entire
large answers through a live region. Existing visible focus indicators are retained.

Mobile layouts stack mode/buttons, wrap long hashes and answer text, and preserve
labels and contrast. History has a comfortable reading width and no nested automatic
scrolling that steals page navigation. No extra UI library is installed. Lazy loading
occurs only when a user opens chat; no inference blocks route navigation. Raw evidence
is retained only in bounded state for citation matching and never rendered wholesale.

## Verification and manual use

From frontend/:

```sh
npm test
npx tsc -b
npm run build
npm run lint
node tests/browser-chat-smoke.mjs
```

Chromium smoke requires the existing `/usr/bin/chromium`; it starts a temporary local
Vite fixture and mock API, not live accounts/providers, and cleans up both processes.
It covers actual textarea/button/key interaction, mode/fallback labels, citation
expansion, stale/missing/limited answers, XSS/unsafe links, duplicate prevention,
cancellation/clear with late response, retries/429 cooldown, visibility denial,
390px mobile layout without horizontal overflow, refresh with no transcript storage,
and project navigation/unmount cleanup. An optional diagnostic screenshot is written
outside the checkout at `/tmp/opendev-chat-mobile.png`. This is Chromium functional
verification, not a complete screen-reader audit or live backend/browser acceptance.

With the isolated local backend running and a synthetic active project, open its
existing details page and choose “Open accountability chat”. As a signed-out visitor,
try the suggestions, compare funding/roadmap answers and source API paths, expand
limitations, and inspect the mode label. Select Auto with no model configured and
check deterministic fallback. Select LLM and verify provider-unavailable messaging;
only a separately configured, successful provider response may be labeled LLM.
Try Shift+Enter, cancellation, clear, navigation, 429 errors and mobile zoom/keyboard
navigation. Compare approved/public versus private evidence using existing document
publication controls outside chat; no document download occurs through chat.

From backend/ with existing local opendev_test_* configuration run the full pytest
suite and Alembic upgrade/check. No new backend files or migrations belong to Step 5.
The preserved Step 4 work remains under test. No paid/live model, private storage,
production financial data, production migration, deployment, commit or push is used.
Live Ollama inference **was not run**. Deployment remains **NO-GO**.

## Recorded results and remaining limits

2026-11-03 local verification:

- **380 backend tests passed, 0 failed/skipped**, 200.14 seconds, including the
  preserved financial/development evaluation datasets. Backend code was unchanged
  during Step 5; read-only/public authorization regressions remain covered.
- **55 frontend tests passed, 0 failed/skipped** (26 preceding + 29 chat cases).
  TypeScript, production build and lint passed. Only the two existing AuthContext
  warnings and existing large lazy Gantt warning remain.
- Chromium/CDP mock-API smoke passed all four named groups, including navigation
  cleanup. The 390px diagnostic screenshot was inspected with readable wrapping,
  disclosure controls and no horizontal overflow. This does not replace a full
  screen-reader, Safari/Firefox, zoom/IME or hosted HTTPS acceptance review.
- Local Alembic upgrade/check passed without drift (head `8c6072dabc59`), and
  whitespace checks passed. No schema migration was added.
- The lazy chat chunk is approximately **15.05 KB / 5.55 KB gzip JS**, plus
  **2.37 KB / 0.91 KB gzip CSS**. No dependency changes; existing Gantt assets remain.

Each answer is independent, not conversational reasoning. History is capped and
volatile. Existing backend page/context/time limits may return constrained or
unsupported answers. Source hashes are displayed rather than recomputed, and
semantic correctness/source authenticity are not certified by citations. Public
visibility is rechecked on queries/source navigation, not continuously polled: an
already displayed formerly public answer stays until clear/navigation or a denial
response. No retroactive revocation or private-source access claim is made.
Browser cancellation may leave backend cleanup/inference in progress. No streaming,
live model acceptance, hosted CI, production migration, deployment, commit or push
was performed. All inherited NO-GO gates remain open.
