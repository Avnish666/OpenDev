# Six-minute OpenDev walkthrough

Audience: hackathon reviewers. Default mode is **local synthetic Community demo**.
Have [demo setup](demo-setup.md) complete, the private manifest at hand and the
[recording narration](submission/demo-script.md) beside the browser. All currency
and GitHub observations shown are fixtures. No live provider acceptance is implied.
This sequence totals 6:30; omit optional Studio in the normal recording.

| Time | Screen / action | Show and say | Expected result / fallback |
| --- | --- | --- | --- |
| 0:00–0:30 | `/#/explore` | Backers need evidence connecting funding, published spending and delivery. Maintainers need a transparent reporting workflow. | Two `[LOCAL DEMO]` campaigns. If unavailable, restart the documented local services; use captured screenshots only while saying they are previously captured local evidence. |
| 0:30–1:00 | `/#/create`, then terminal test result, then main project | GitHub normally handles login and repository ownership. Signed-out creation stays protected. Explain the cookie-authenticated HTTP fixture journey. | Sign-in requirement, no bypass. The local test mocks only external GitHub/provider replies; do not narrate this as browser OAuth success. Live login is unverified. |
| 1:00–1:40 | `/#/projects/<project_id>` → Backer Rewards; then Open financial transparency ledger | Campaign goal/budget and unlimited reward tier. Explain Sandbox Orders v2, server-derived prices and signature-verified idempotent callbacks. | No checkout click. Fixture gross 1100 USD, refund exclusion 50, reversal 100, net 950. Show integration source diagram if asked; real Sandbox/webhook delivery NOT RUN. |
| 1:40–2:25 | Ledger → Hosting expense, or `/#/projects/<project_id>/expenses/<expense_id>` | Reports and supporting evidence are distinct. One Hosting overrun is public; private receipt/review details stay private. Explain PDFium/pypdf/Tesseract extraction as a separate private pipeline. | Spending 650 USD, Hosting 250 vs 200 budget, public overrun 50. Approved fixture metadata only; no stored object/download. For actual native extraction use the synthetic offline OCR smoke result, explicitly outside this public web demo. |
| 2:25–3:15 | Project → GitHub activity → Roadmap / timeline → Timeline, Month scale | These are retained, dated fixture observations, not live updates. A closed issue or merged PR does not certify delivery. Show the Gantt dependency and a revised deadline. | Three commitments: asserted delivery 2026-10-04 vs original 10-05; documentation revised 10-10 → 10-20 and unfinished; feedback planned through 2027-12-01. Overdue days change with UTC date. If beta Gantt fails, Milestone list and history remain the text fallback. |
| 3:15–3:40 | Main project maintainer link → `/#/maintainers/<owner_id>` | Keep owner outcomes, repository signals and reward fulfillment distinct. | Active public owner aggregate includes both fixture projects, including current campaign; no previous-project cohort or trust score. One of two eligible entitlements fulfilled, maintainer-asserted. |
| 3:40–4:35 | `/#/projects/<project_id>/analytics` | Community financial charts and grid → Spending & Evidence → Development Progress → Maintainer Analytics. Apply a Hosting filter, download expenses CSV, then reset. | Values match ledger; filters affect documented dimensions, not all project totals. CSV contains only published rows. If charts fail, the exact-value tables remain. Studio is omitted by default; see separate evaluation below. |
| 4:35–5:55 | Return project → Open accountability chat → choose Deterministic | Ask funding, deadline and missing-information questions; expand Evidence citations and follow a permitted public source. | Returned mode **Deterministic**, not LLM. Funding is 95000 USD minor units. Citations identify actual public fixture projections; relevance/completeness is not certified by a hash. For a clear short recording, ask one question live and show the question matrix for the others. |
| 5:55–6:30 | Ledger/overview, then limitations/checklist | OpenDev makes reporting inspectable while keeping claims bounded. Explicitly state what is implemented and what remains unverified. | Local demo GO; public deployment NO-GO. No escrow, bank-balance, fraud, independent-delivery, production-readiness or sponsor-eligibility claim. |

The screen order is exact, but IDs come from the manifest. The UI uses hash routing;
`/analytics` and `/roadmap` are suffixes within the project hash. Financial transparency
opens through **Open financial transparency ledger**, not automatically on page load.
Use **Read milestone history** on a milestone to inspect the recorded original/revised dates.
If a label differs, inspect the visible control; do not bypass access checks.

## Scripted deterministic questions and actual fixture expectations

Use these exact supported wordings. More natural paraphrases can return
unsupported_question; do not silently imply general LLM understanding.
[Captured backend responses](submission/demo-answers.json) are actual test output from
public synthetic data, including dynamic evaluation dates. They are not invented scripts.

| Narration prompt | Exact question to enter | Expected evidence / limitation |
| --- | --- | --- |
| Financial: recorded funding | How much funding has the project received? | 95000 USD minor units; not a verified balance. |
| Financial: allocation of published spending | What is the reported spending by category? | Development 35000, Hosting 25000, Documentation 5000 cents against existing allocations. |
| Financial: unresolved public findings | What discrepancies have been publicly disclosed? | One Hosting category overrun; public budget facts, not private receipt findings or fraud allegations. |
| Development: overdue | Which milestones are overdue? | Documentation/release is unfinished beyond 2026-10-20; UTC evaluation date is shown. |
| Development: deadline changes | Which commitments were delayed or rescheduled? | Original 2026-10-10 retained, current 2026-10-20; revision count one. |
| Development: supporting GitHub evidence | What GitHub activity is available? | One closed issue, one merged PR, one sampled commit; fixture sync dated 2026-10-01 and stale. Inspect roadmap linked evidence for attribution. |
| Cross-domain: spending vs delivery | Are the reported expenses increasing while delivery is delayed? | Published spending plus current roadmap/delay facts; insufficient time-series/causal evidence for an increasing-spend claim. Safe insufficient_evidence is a successful limitation, not a fabricated trend. |
| Cross-domain: what remains unverified | What financial information is missing? | No verified bank balance/vendor payment, incomplete exact refund history and withheld private evidence. Pair with “What evidence is missing to assess delivery?” if needed. |

For the funding-plus-overdue comparison, the supported optional question is
“How much funding has this project received, and which commitments are overdue?”
It uses both financial and roadmap sources without inferring misuse of funds.

## Optional sponsor and model segments

AG Studio may replace 20–30 seconds of the analytics segment **only if a permitted
local evaluation is installed and the intended recording/sharing is allowed by the
actual terms**. Use the separate loopback evaluation browser journey in
[sponsor integrations](submission/sponsor-integrations.md), show the genuine trial
notice, label it evaluation and retain Community as the default. No evaluation
screenshot was captured for this submission package. Do not claim the Community
renderer is Studio or publish commercial evaluation bundles as a free deployment.

For approved local Ollama, follow [Step 5's explicit acceptance procedure](phase7-ai-capacity-verification.md#13-exact-future-local-commands)
on owner hardware in a separate synthetic test server. No install/pull is automated.
Until a real model runs, say **real Ollama inference NOT RUN**. Do not replace the
mode label or splice a deterministic response into a supposed live model sequence.
