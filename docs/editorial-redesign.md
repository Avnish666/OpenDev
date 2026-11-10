# OpenDev editorial frontend redesign — handoff

## Outcome and direction

The application now uses an editorial public directory and a compact financial
workspace: warm paper, charcoal type, restrained blue, DM Sans and Instrument
Serif. Light mode is the primary direction; dark mode uses neutral charcoal.
The visual composition is deliberately different from the previous split hero,
navy workflow diagram, feature sequence and repeated rounded campaign cards.

`design-taste-frontend` was not present in the available skill catalog or local
skill directories. The user's explicit fallback was followed; no claim is made
that its proprietary workflow, inspection tooling or `--app` command was used.

The existing React/Vite application, hash routes and integrations are retained.
No backend, database, API client, authentication, payment, model/provider or
scheduling implementation was changed. No commits, pushes or deployment occurred.

## Structural and presentation changes

- **Homepage/discovery:** short typographic introduction, actual API projects
  immediately below, first-project editorial article, then ruled directory rows.
  The first item is not presented as curated or independently verified. The
  directory uses only available fields; repository owner is explicitly labeled.
  Funding totals and maintainer names are not invented from the list response.
  Existing page-scoped search and pagination remain explicit and functional.
- **Shell:** original bracket mark, restrained navigation, underlined current
  route, compact Create Project action, theme control and account/mobile menus.
  Existing mobile focus, Escape and authentication behavior are retained.
- **Project workspace:** compact identity, section index, recorded funding,
  reported spending and calculated difference before the campaign plan and
  rewards. Development context, provenance, source limitations, immutable history,
  public ledger, assistant and analytics remain available. Funding summaries and
  reward controls compose without remounting rewards during summary refreshes.
- **Rewards/funding:** pricing columns, contribution records instead of generic
  cards, a paper-like return/receipt layout, independently labeled contribution
  and entitlement states, prominent Sandbox disclosures and original actions.
- **Analytics:** integrated toolbar, compact filter scope, horizontal financial
  register, restrained chart canvases, aligned tables and document coverage.
  Chart/grid colors and fonts follow the new themes. Exact amounts, data scope,
  licensing gates, safe-chart-range checks and empty/error states remain intact.
- **Assistant:** evidence notebook with composer first on mobile and suggested
  questions beside it on desktop. Questions, findings and indexed citations use
  a shared reading axis rather than alternating bubbles. Requested/returned modes,
  freshness, source hashes, uncertainty, cancellation, retry and privacy remain.
- **Maintainers/forms:** unnumbered ruled field groups, plain guidance column,
  consistent controls, readable expense records and public track-record sections.
  Existing names, constraints, validation and submission payloads remain unchanged.
- **Bryntum:** compact toolbar, local timeline overflow, selected milestone
  detail and schedule confirmation surfaces; SDK scheduling behavior preserved.

The shared component addition is `ProjectListing.tsx`. `UI.tsx` primitives were
refined; internal FundingSnapshot and DevelopmentSnapshot compose the existing
public progress data. DESIGN.md documents alternatives, the chosen direction,
tokens, type licensing, compositions, product boundaries and verification rules.

## Browser review and screenshots

The actual React application was rendered in `/usr/bin/chromium`, using Vite and
isolated synthetic API fixtures. No live financial data or provider was altered.
A FastAPI backend was not listening on port 8000, so these checks do not establish
live OAuth, PayPal, GitHub, Ollama or storage acceptance.

Before screenshots were captured from clean HEAD `c895d12`. Three visual review
passes were completed, followed by final verification:

1. Replaced the homepage/card composition and reviewed mobile/tablet/desktop
   output. Found a tall feature treatment, misplaced financial hierarchy, awkward
   assistant spacing and unsupported arrow glyphs.
2. Moved recorded financial values before campaign/reward context, tightened the
   featured article, fixed source alignment and replaced missing arrow glyphs.
   The next review identified the mobile composer's position below suggestions
   and overly tall analytics filter/scope presentation.
3. Moved the composer first, placed desktop suggestions alongside it, compacted
   filter scope, preserved reward state during refresh and refined data density.
   Final finishing aligned chart typography and preloaded the self-hosted UI font.

The comparison gallery is `/workspace/work/editorial-review/index.html` and its
portable archive is `/workspace/work/opendev-editorial-review.zip`. It contains
**138 before + 138 after images**: 23 screens × 390/768/1440px × both themes.
The three intermediate review capture sets are also retained under
`/workspace/work/editorial-pass1`, `editorial-pass2`, and `editorial-pass3`.
These bulky QA artifacts are kept outside the repository.

Screens covered: landing, discovery, project, rewards, empty/answered chat,
timeline, financial transparency, analytics, charts, public expense evidence,
create project, account menu, My Projects, maintainer profile, funding history,
funding return, receipt, edit project, expense reporting, reward editor, roadmap
management and GitHub sync.

## Tests and accessibility

All final checks passed:

| Check | Result |
| --- | --- |
| `npm test` | 89 passed, 0 failed |
| `npx tsc -b` | Passed |
| `npm run lint` | Passed; 2 pre-existing AuthContext warnings |
| `npm run build` | Passed; existing heavy SDK chunk warning |
| `npm run test:design-browser` | 23 scenes × 5 widths × 2 themes; 0 runtime exceptions, 0 unexpected API requests |
| `node tests/browser-theme-smoke.mjs` | Keyboard toggle, persistence, OS independence, storage failure/cross-tab handling, menus, protected routes, SDK themes |
| `node tests/browser-chat-smoke.mjs` | Modes/fallback badges, safe citations, submit/newline, cancel/late results, retry/rate limit, privacy and mobile layout |
| `node tests/browser-analytics-smoke.mjs` | Real Community charts/grid, filter/reset/pagination, CSV, licensing gate, empty/error recovery and public routes |
| `node tests/browser-gantt-smoke.mjs` | Real drag/resize, explicit confirmation, versioned save, conflict/server-error recovery, read-only scope, timezone and hostile-title escaping |
| Source AST comparison | 15 async handlers across 11 workflow modules unchanged; API calls and effects unchanged |
| `git diff --check` | Passed |

The design matrix checks 360, 390, 768, 1280 and 1440px in both themes for page
horizontal overflow, overlapping grid items and app button touch targets. Browser
checks include visible focus, mobile menu focus/escape, reduced motion, long exact
financial values, labels and actual chart/grid/Gantt theme changes. Tables and
timelines retain their own local scroll regions. This is not a full assistive
technology audit.

Measured design-token contrast ratios:

| Pair | Light | Dark |
| --- | ---: | ---: |
| Body/background | 14.14:1 | 14.30:1 |
| Muted/surface | 5.44:1 | 7.29:1 |
| Link/surface | 5.99:1 | 7.55:1 |
| Primary button text | 4.98:1 | 5.24:1 |
| Input boundary/surface | 3.24:1 | 4.01:1 |

Two failures were investigated during verification. The theme smoke waited for a
removed marketing headline; its readiness condition now verifies the actual
analytics route and working project link, preserving all behavioral assertions.
The analytics smoke caught an eager repository URL read in the new listing;
the component now preserves the prior unavailable-repository fallback. That
fixture was not changed. The original analytics test passes after the code fix.
No tests were removed or skipped.

## Measured build changes

Same production build process and Node gzip settings, decimal bytes:

| Asset scope | Before | After | Difference |
| --- | ---: | ---: | ---: |
| Main JS | 303,313 | 299,245 | −4,068 |
| Main CSS | 42,375 | 30,900 | −11,475 |
| All JS/CSS | 5,325,861 | 5,306,265 | −19,596 |
| All JS/CSS gzip | 1,526,035 | 1,521,944 | −4,091 |
| Added self-hosted fonts | 0 | 80,092 | +80,092 |

Including the fonts, total changed code/font assets grow by 60,496 raw bytes.
Fonts are Latin WOFF2 subsets with swap behavior and local licenses; DM Sans is
preloaded. Existing Font Awesome vendor assets are unchanged and excluded equally
from the comparison. Bryntum (~1.95 MB) and the Community analytics renderer
(~2.57 MB) remain lazy; their existing bundle warning remains. No dependency was
added or removed. Measurements are in
`/workspace/work/editorial-bundle-comparison.json`.

## Files changed

- `DESIGN.md`, `docs/editorial-redesign.md`
- `frontend/index.html`
- `frontend/src/index.css`, `frontend/src/App.css`, `frontend/src/App.tsx`
- `frontend/src/design/product.css`, `frontend/src/design/analyticsTheme.ts`
- `frontend/src/components/ProjectListing.tsx` (new)
- `frontend/src/components/UI.tsx`, `frontend/src/components/ProjectProgress.tsx`
- `frontend/src/components/ProjectAIChat.tsx`, `frontend/src/components/ProjectAIChat.css`
- `frontend/src/components/ProjectAnalytics.tsx`, `frontend/src/components/ProjectAnalytics.css`
- `frontend/src/components/ProjectAnalyticsCommunity.tsx`
- `frontend/src/components/RoadmapTimeline.css`, `frontend/src/components/Transparency.css`
- `frontend/src/pages/Projects.tsx`, `frontend/src/pages/Funding.tsx`, `frontend/src/pages/Maintainer.tsx`
- `frontend/src/assets/fonts/dm-sans-latin-variable.woff2`
- `frontend/src/assets/fonts/instrument-serif-latin.woff2`
- `frontend/src/assets/fonts/instrument-serif-latin-italic.woff2`
- `frontend/src/assets/fonts/DM-Sans-OFL.txt`, `frontend/src/assets/fonts/Instrument-Serif-OFL.txt`
- `frontend/tests/browser-design-smoke.mjs` (768px captures and font readiness)
- `frontend/tests/browser-theme-smoke.mjs` (route readiness instead of removed copy)

## Remaining limits and startup

The directory API has no funding totals or maintainer display name; those are not
invented. SDK internals retain vendor interaction conventions. AG Studio's
unauthorized/unavailable state was verified; no licensed live deployment is claimed.
The browser evidence uses synthetic data and does not verify live services.
There are no known global-overflow, card-overlap or runtime failures in the tested
matrix; untested assistive technology/browser combinations may need further review.

Start the frontend against the existing backend/proxy configuration:

```sh
cd /workspace/OpenDev/frontend
npm run dev -- --host 127.0.0.1
```

The existing Vite proxy expects the separately configured backend on port 8000.
To regenerate isolated browser evidence without live services:

```sh
cd /workspace/OpenDev/frontend
OPENDEV_SCREENSHOT_DIR=/workspace/work/editorial-final npm run test:design-browser
```
