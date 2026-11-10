# OpenDev — an editorial financial operating system

## Decision and alternatives

The previous split hero, navy workflow illustration, repeated feature steps and
rounded campaign cards postponed the real product and made unrelated information
look alike. The redesign begins with actual projects and separates a public
directory from a financial/development workspace.

Three directions were compared before implementation:

1. **The ledger:** compact numerical registers and ruled tables. Strong for finance,
   too severe for first-time discovery on its own.
2. **The dispatch:** an editorial introduction, a prominent actual project, then a
   structured directory. Strong discovery and distinct typography, but needs more
   operational density on authenticated screens.
3. **The command center:** conventional sidebar/dashboard panels. Familiar, but
   reproduces the generic application composition the redesign must replace.

The chosen direction combines the dispatch for discovery with the ledger for
application screens. Warm paper, charcoal type, thin rules and controlled blue
links create the identity. Dark mode uses neutral charcoal, not layered navy.
There is no decorative workflow, marketing feature sequence, invented chart or
fictional campaign. The first available project is prominent because of its place
in the current API page; it is not described as curated, verified or recommended.

## Product and information boundaries

Project discovery has only title, description, repository, owner ID, status, goal
and currency. It must not imply funding totals or a maintainer identity that the
list API does not supply. Repository namespace is labeled as a repository owner.
Recorded funding appears where the existing progress/financial API supplies it.
Search explicitly filters the current page. Pagination requests remain unchanged.

Money is server-derived. Recorded Sandbox funding, maintainer-reported spending,
calculated difference, document support and independent verification remain
separate concepts. Do not use a trust score or imply a bank balance. The returned
chat execution mode is always visible and accurate. All evidence, timestamps,
source limitations, safety checks, checkout disclosures and licensing behavior
remain present. Backend, authentication, payment, scheduling and request logic are
outside this visual redesign.

## Typography and assets

- **DM Sans**, variable 400–700: body, navigation, controls, data, tables, headings.
- **Instrument Serif**, regular/italic: editorial opening and featured project title.
- Body 15px/1.6; supporting text 12–13px; field labels 12px; table data 12–13px.
- Editorial heading 44–72px, 1.03 line height; page 30–42px; section 22–28px.
- Money 28–38px with tabular numerals; exact long values wrap rather than truncate.

Latin WOFF2 subsets are self-hosted in `frontend/src/assets/fonts`, with original
SIL Open Font License files. No Google Fonts runtime request. Fallbacks support
characters outside these subsets. Use at most these two designed font families;
monospace remains a system fallback for hashes/code. Font loading uses swap.

## Tokens

`frontend/src/index.css` owns typography, colors, spacing, radii and motion.
`frontend/src/design/analyticsTheme.ts` resolves matching colors for SDK canvases
and AG Grid. Light: warm #F6F5F1, white surfaces, #20252B text, #1469E8 accent.
Dark: charcoal background/surfaces with warm neutral text and accessible blue.
Muted type targets 4.5:1, input boundaries 3:1, focus is visibly blue.

Spacing: 4, 8, 12, 16, 20, 24, 32, 40, 48, 64px. Controls use 4px radii;
functional panels 6px. Status indicators are small text/dot labels rather than
pill-shaped decoration. Thin dividers replace repeated card boundaries. Shadows
are reserved for popovers. Buttons and primary interactive controls are at least
44px high. Blue means action or selection; semantic colors mean actual state.

## Compositions and reusable primitives

`UI.tsx` supplies PageHeading, SectionHeading, MetricCard, StatusBadge, FormSection
and EmptyState. `ProjectListing` presents the same genuine project fields in a
featured article or ruled row. The feature treatment is limited to discovery;
maintainer and analytics selection screens remain compact.

- **Shell:** original bracket mark and wordmark, restrained top navigation,
  underlined current route, Create Project action, persistent theme control,
  keyboard-operable account disclosure and mobile navigation.
- **Opening:** single editorial headline and a short explanation. No split hero,
  illustration or redundant feature strip. Actual project content follows directly.
- **Directory:** a first-project feature with repository and campaign target;
  remaining projects are readable records, with consistent status/goal/action.
- **Project workspace:** compact identity, horizontal section index, a funding
  plan and reward area, followed by a public evidence register and operational
  tools. Primary funding/spending/difference values are easy to scan.
- **Analytics:** integrated controls, compact metric registers, paired chart
  canvases and locally scrollable tables. Calculation scope and reconciliation
  stay available, including visible funding goal. Community SDKs are preserved.
- **Assistant:** an evidence notebook. Questions and answers are records, not
  alternating bubbles. Suggestions are text rows; citations are indexed source
  entries; requested/returned modes and source uncertainty are explicit.
- **Forms:** ruled field groups with short explanatory notes, unnumbered titles,
  aligned action footer and a plain secondary guidance column. Original field
  names, constraints, validation and payloads remain unchanged.
- **Funding:** contribution records and restrained receipt layout; payment status
  and reward entitlement remain independently labeled. Sandbox remains prominent.
- **Roadmap:** compact surrounding toolbar and selected-record detail. SDK DOM,
  drag/resize, confirmation, immutable history and persistence remain untouched.

## States, responsiveness and motion

Empty states explain what records would populate the view and offer an appropriate
existing action. Loading uses a small indicator or flat skeleton, not decorative
charts. Errors retain original recovery and cancellation behavior. Native details
provide accessible source/calculation expansion. Visible focus, skip link and
existing mobile focus/escape behavior are retained.

Maximum content width 1440px with 24–64px gutters. At 1100px navigation collapses;
at 900px directory metadata rearranges; at 767px records and forms become single
column. Tables/timeline scroll within their own region. Check 360, 390, 768, 1280
and 1440px in both themes. Interactive transitions are 160–220ms; no continuous
marketing animation. Respect prefers-reduced-motion globally, including SDK shells.

## Verification

Use the actual React application in Chromium with isolated synthetic API fixtures
when a live backend is unavailable. Never alter real financial records. Capture
before/after at 390, 768 and 1440px in both themes. Perform three visual review
passes and record findings/fixes. Run unit, TypeScript, lint, production build and
existing browser contracts for theme, chat, analytics and Bryntum. Measure actual
JS/CSS and added font bytes; keep heavy SDK renderers lazy. Do not describe fixture
screenshots as live-provider acceptance or independent evidence verification.
