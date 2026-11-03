# Recording script — target 6:30

**Recording status: not recorded.** This is narration and a precise screen sequence,
not a claim a video exists. Use the [walkthrough](../demo-walkthrough.md) and manifest
IDs. Keep a visible “local synthetic demonstration” caption in the recorded video's
editor/title card; do not modify the application's returned mode or evidence.

| Segment | Screen/action | Suggested spoken narration |
| --- | --- | --- |
| 0:00–0:30 · Problem | Explore Projects, two `[LOCAL DEMO]` cards | “OpenDev connects open-source funding with inspectable reporting. Backers can examine spending and commitments; maintainers can show evidence. Every record in this demonstration is synthetic local data.” |
| 0:30–1:00 · Identity and creation | Create Project signed-out screen, then the existing normal-cookie HTTP journey result | “GitHub OAuth and repository ownership protect project creation. This local setup has no live OAuth credentials, so the UI correctly requires sign-in. Our separate HTTP integration test exercises state validation, real hashed sessions and project creation with mocked external replies. This is not live browser OAuth acceptance.” |
| 1:00–1:40 · Funding/rewards | Main campaign budget and Backer Rewards, then ledger | “Reward tiers determine prices in backend code. PayPal Sandbox order, capture and signature-verified callback handling are implemented and tested with mocks. These fixture records show 1100 dollars gross, a 50-dollar known refund exclusion, a 100-dollar reversal and 950 dollars net recorded. No checkout transaction is performed.” |
| 1:40–2:25 · Reports/evidence | Financial transparency and Hosting expense metadata | “Maintainers reported 650 dollars of spending. Hosting exceeds its 200-dollar allocation by 50. One expense has approved redaction metadata; two have no public evidence. Original receipts and private review details stay private. This demo has metadata, not Supabase objects. Separate native PDFium and Tesseract fixture tests passed, but receipt support does not prove vendor payment.” |
| 2:25–3:15 · Development | GitHub activity, Timeline/Month, then Read milestone history | “These dated GitHub observations are fixtures and are marked stale. The Bryntum Community Gantt shows commitments and a dependency. The documentation deadline moved from October 10 to October 20; original history remains. Delivery is a maintainer assertion, not an automatic consequence of a closed issue or merged PR.” |
| 3:15–3:40 · Outcomes | Maintainer profile | “Delivery timing and rewards have explicit samples and denominators. One of two eligible completed-capture entitlements is marked fulfilled. The owner aggregate covers currently active projects, including this one; it is not a lifetime trust score or an independent previous-project comparison.” |
| 3:40–4:35 · Analytics | Analytics → Community → Financial / Spending / Development / Maintainer; Hosting filter; expenses CSV | “AG Grid and Charts Community reuse the same public projections, with documented filters and a CSV export. Values match the ledger. Optional AG Studio 3.0.0 is implemented in an isolated commercial evaluation adapter; it is not this Community renderer and has no verified public license.” |
| 4:35–5:55 · Cited answers | Open accountability chat, Deterministic, funding question; expand citations | “The returned mode is Deterministic. The answer uses 95000 USD minor units from current authorized fixture records, with a public-source citation. We can also inspect revised deadlines and missing information. Numerical accounting stays in backend code. A citation hash identifies a projection, not semantic truth. Real Ollama inference has not run.” |
| 5:55–6:30 · Conclusion/limits | Overview, then submission checklist | “OpenDev makes funding and reporting easier to inspect without pretending reports prove payment or delivery. The local demonstration works without paid services or live credentials. Public deployment remains NO-GO pending credential, licensing, containment, real-provider and hosting acceptance. This is an honest demonstration of the implemented system and its limits.” |

Use the exact questions in the walkthrough. For a second answer, choose
“Which commitments were delayed or rescheduled?” or “What financial information is missing?”
If a free-form cross-domain question is unsupported, use its mapped exact intent;
never claim the deterministic baseline understands arbitrary natural language.

Optional Studio: substitute at most 20–30 seconds of analytics only after reviewing
permission for local evaluation **and recording/sharing**. Show genuine SDK trial
notices and label the segment. Otherwise show the source matrix and Community only.
Optional Ollama: record a separate real local run only after owner-approved installed
model acceptance; do not splice synthetic/mock responses into supposed real inference.

Before recording, close developer tools containing cookies/headers and other browser
profiles; use only synthetic identities and public data. Preserve privacy labels,
actual execution mode and limitation messages. No stock/fake application screenshots,
private receipt views, invented provider success or fabricated submission URL.
