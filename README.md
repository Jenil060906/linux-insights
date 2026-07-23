# Linux Insight

Intelligent Linux Observability Platform — a dark-theme monitoring dashboard for Linux servers.

This repo is a monorepo laid out for the full product (agent → API → dashboard), but **only the `frontend/` is implemented so far**. Everything else is a reserved, empty scaffold for later phases. The frontend currently runs entirely on a mock data layer — there is no backend, no agent, and no real authentication yet.

## Repository layout

| Directory | Status | Purpose |
|---|---|---|
| `frontend/` | **Implemented** | React dashboard UI — see below |
| `backend/` | Scaffold only | Future API server (`app`, `api`, `database`, `models`, `services`, `websocket`) |
| `linux-agent/` | **Skeleton only** | Host-side metrics collector — project structure exists, no monitoring code yet. See below |
| `docs/` | Scaffold only | Architecture notes, API docs, UI design references |
| `scripts/` | Scaffold only | Future dev/ops tooling |
| `tests/` | Scaffold only | Future cross-package test suites |
| `reports/` | Scaffold only | Future generated reports |

## Frontend

### Tech stack

- React 19 + Vite 6 + TypeScript (strict)
- Tailwind CSS v3 — design tokens live in `tailwind.config.ts`, not CSS variables
- shadcn/ui-style primitives (`components/ui`) + `class-variance-authority` for variants
- Recharts (code-split via `React.lazy`) for the live monitoring chart
- Framer Motion for transitions and live-data animations (`MotionConfig reducedMotion="user"` at the app root)
- React Router v7 for client-side routing
- Lucide React for icons

### Getting started

```bash
cd frontend
npm install
npm run dev       # start the dev server
npm run build     # typecheck (tsc -b) + production build
npm run lint       # eslint
```

### App flow

- **`/` — Login / server discovery.** A UI-only flow: a placeholder list of "discovered" servers with a searching animation, plus a manual-connect form (server name, optional IP/port). No networking happens — "Connect" stores a dummy server record in `localStorage` (`linux-insight:selected-server`) and navigates to `/dashboard`. If a server is already selected, `/` redirects straight to `/dashboard`.
- **`/dashboard` — The monitoring dashboard.** Renders once a server is "selected." Logout clears `localStorage` and returns to `/`.

The login feature (`src/features/login/`) is deliberately self-contained with its own types and mock data, kept decoupled from the dashboard's data layer until a real connection flow replaces both.

### Dashboard sections

- **Header** — host identity, connection status, logout
- **System Health Hero** — overall health score and status
- **Metric Cards** — CPU / Memory / Disk / Network, live-updating
- **Live Monitoring** — a switchable, real-time usage chart
- **AI Insights** — anomaly/recommendation feed
- **Alerts** — active alert list
- **Top Processes** — process table ranked by CPU
- **Quick Actions** — common operator actions (non-functional placeholders)
- **Analytics** — historical trend/breakdown panels (placeholder)
- **Logs** — filterable system log feed

### Design system

All design tokens (color, typography, radius, shadow, 8px spacing scale) are defined once in `frontend/tailwind.config.ts` with rationale comments, and consumed through reusable primitives:

- `components/ui/` — `Button`, `Badge`, `Card`, `StatusIndicator`, `IconTile`, `Skeleton`, `Input`
- `components/common/` — `SectionCard`, `Chip`, `UsageBar`, `MiniSparkline`, `FadeIn`, `PlaceholderCard`, `EmptyState`
- `charts/` — `UsageAreaChart` (Recharts), `ChartSkeleton`, shared `chartTheme`

Dark theme only. Every icon-only control has an `aria-label`; decorative icons are `aria-hidden`; custom animations respect `prefers-reduced-motion` via `motion-safe:`/`MotionConfig`.

### Mock data layer

All placeholder data lives in `src/mock/`, one file per domain, and every export is a **function** rather than a bare constant:

```
src/mock/
├── server.ts        getHostInfo(), getSystemHealth()
├── metrics.ts        getMetricCards(), getLiveMonitoringSeries(), buildLiveMetricCards()
├── liveDataSource.ts  LiveDataSource interface + mockLiveDataSource (random-walk generator)
├── alerts.ts          getAlerts()
├── processes.ts       getProcesses()
├── analytics.ts       getAnalyticsPanels()
├── insights.ts        getAiInsights()
├── logs.ts             getLogEntries()
└── quickActions.ts    getQuickActions()
```

Every dashboard component takes its data as an optional prop that defaults to the matching mock getter (`metrics = getMetricCards()`), so components stay presentational and are usable in isolation. Replacing mock data with a real API later means changing a function body from sync to async — e.g.:

```ts
// today
export function getAlerts(): AlertItem[] { return alerts; }

// later
export async function getAlerts(): Promise<AlertItem[]> {
  const res = await fetch("/api/alerts");
  return res.json();
}
```

— not rewriting call sites.

### Simulated live monitoring

Metric Cards and the Live Monitoring chart are wired to a simulated live stream instead of a frozen snapshot:

- `src/mock/liveDataSource.ts` defines a `LiveDataSource` interface (`getNextValue(metric, previousValue)`) and a `mockLiveDataSource` implementation that random-walks each metric within a realistic range once per tick.
- `src/hooks/useLiveMetrics.ts` ticks once a second, appends a new sample per metric to a rolling window, and is the **only** place that knows how new values arrive. A future WebSocket/SSE/polling client implements the same `LiveDataSource` interface and swaps in here — no other component changes.
- `DashboardPage` calls `useLiveMetrics()` once and passes the result down to both `MetricCardGrid` and `LiveMonitoringSection`, so the two stay in sync and both remain plain, prop-driven components with static-mock defaults for standalone use.
- `src/hooks/useAnimatedSeries.ts` tweens sparkline values between ticks (`requestAnimationFrame`-based), and the Recharts area chart has its built-in transition animation enabled, so every update animates smoothly instead of snapping.

### Responsiveness

Layout is audited for phone, tablet, laptop, and large-desktop widths: no horizontal scrolling, grid columns collapse progressively (`sm:`/`lg:` tiers), typography scales, and desktop appearance is unchanged from the original design.

### UI polish pass

A visual-QA pass across the whole app (dashboard + login) fixed a handful of small inconsistencies without touching layout or functionality:

- **Icon proportions** — `IconTile`'s icon glyph now scales with tile size instead of staying a fixed 16px; the `lg` tile (used by Quick Actions) previously looked under-filled at 36px with only a 16px icon.
- **Empty states** — Alerts and Logs each had their own hand-rolled "nothing here" markup that didn't match (one dashed-boxed, one not). Both now use a shared `EmptyState` component (icon + message), consistent with the box-and-icon language `PlaceholderCard` already established elsewhere.
- **Hover feedback** — Metric Cards (CPU/Memory/Disk/Network) previously had no hover treatment at all despite now showing live-updating data; they get a subtle shadow lift (`hover:shadow-soft`) so the tiles read as active, not static wallpaper.
- **Transitions** — `UsageBar`'s fill now animates width changes instead of snapping, matching the animated-update treatment used everywhere else data can change.
- **Dead CSS** — removed a no-op `hover:border-border` on `Chip` (declared a hover override equal to its own resting value).

### Senior-engineer refactor pass

A structural review (folder structure, component reuse, performance, accessibility, naming, TypeScript, Tailwind) found and fixed four real issues — no behavior or visual output changed; verified via `tsc -b`, `eslint`, and a byte-identical CSS build before/after:

- **Duplicated filter logic** — `AlertsSection` (filter by severity) and `LogsSection` (filter by level) each hand-rolled the same "active filter → per-category counts → filtered list" state and the same filter-chip row markup. Extracted into `src/hooks/useCategoryFilter.ts` (the state/counts/filtering behavior) and `src/components/common/FilterChipRow.tsx` (the chip row), so both sections now consume the same two pieces instead of maintaining parallel copies.
- **Needless re-renders** — `DashboardPage` re-renders every second to drive the live metric tick, which by default re-renders every section beneath it too — including the 7 of 9 sections that receive no live data and have nothing new to show (`SystemHealthHero`, `AIInsightsSection`, `AlertsSection`, `TopProcessesSection`, `QuickActionsSection`, `AnalyticsSection`, `LogsSection`). Wrapped each in `React.memo`; since none of them are ever passed props by `DashboardPage`, they now render once and skip every subsequent tick. `MetricCardGrid` and `LiveMonitoringSection` are intentionally left unmemoized — they're supposed to update every second.
- **Split config maps** — `LogsSection` tracked a log level's icon, text color, and border color in three separate `Record<LogLevel, ...>` objects that had to be kept in sync by key; `Header` did the same (label + status tone) for connection state. Both consolidated into one config map per status enum, matching the pattern `AlertsSection`/`SystemHealthHero` already used.
- **Accessibility** — the "Advanced" disclosure toggle in the manual-connect form had `aria-expanded` but nothing pointing assistive tech at the region it expands; added a matching `id`/`aria-controls` pair.

## Linux Agent

The Linux Agent is the host-side component of Linux Insight: a process that will eventually run on each monitored Linux server, collect system metrics/logs, and report them to the backend. As of Week 2, only the **project skeleton** exists — no collection or monitoring logic has been written yet.

```
├── linux-agent/
│
├── collectors/
├── config/
├── core/
├── README.md
├── requirements.txt
└── main.py
```

- `collectors/`, `config/`, `core/` — empty packages (each holds only an `__init__.py`) reserved for metric/log collectors, configuration loading, and core runtime logic respectively.
- `main.py` — entry point; currently only a module docstring, no code.
- `requirements.txt` — currently empty.
- `README.md` (`linux-agent/README.md`) — explains the agent's purpose and current status in more detail.

## Release review — v0.1 (production readiness)

_Staff-engineer-level review of the frontend as it stands at v0.1, ahead of backend development. Review only — no code changed for this pass._

**Verdict:** solid to ship as a frontend-only preview (no backend, mock data only, clearly labeled as such throughout this README). **Not** yet safe to wire a real backend directly into — a short, concrete list of prep work below should land first, mainly because the current data-fetching story (a default-prop function call) doesn't survive the sync→async transition on its own, and there's no connection-state or error-state model anywhere in the UI yet.

### Design consistency
Strong. One token layer (`tailwind.config.ts`) is the only source of color/type/radius/shadow/spacing, and every component consumes it rather than hardcoding values — confirmed by grep, no stray hex codes outside `charts/theme.ts` (which necessarily mirrors the tokens in raw form because Recharts needs SVG attribute values, not Tailwind classes). Status colors (`success`/`warning`/`danger`/`primary`) are reserved for state and never reused decoratively. Two rounds of dedicated polish passes already closed the gaps that existed (icon proportions, empty-state consistency, hover feedback, dead CSS).

### Enterprise UI quality
Reads as intended — muted dark palette, no glassmorphism/neon, consistent 12px/10px/8px radius scale, restrained shadow use (`shadow-card` default, `shadow-soft` reserved for exactly one hero element per view). Loading states use skeletons, not spinners, everywhere except the one deliberately-permanent "searching" affordance on the login screen. Genuinely the weakest single section visually is **Analytics** — it's two placeholder tiles with no real content, which is honest (better than fake charts) but is the one screen that will look unfinished in a stakeholder demo.

### Responsiveness
Audited for phone/tablet/laptop/desktop; grid columns and breakpoint tiers (`sm:`/`lg:`/`xl:`) were deliberately chosen against actual content width rather than device-guessing, and desktop appearance was preserved throughout that pass. No horizontal scroll anywhere. Not tested against real touch devices (no touch-target sizing pass, no tested behavior for iOS Safari's dynamic viewport bar) — worth a manual pass before a public launch, not before backend integration.

### Routing
Clean and minimal: two real routes (`/`, `/dashboard`) plus a catch-all redirect, guarded by a single localStorage read (`getSelectedServer()`), mapped into the dashboard's `HostInfo` shape at exactly one seam (`App.tsx`). No nested routes, no route params, so there's nothing to get wrong there yet. **Gap:** neither route is code-split (`LoginPage`/`DashboardPage` are both eagerly imported in `App.tsx`), so a user sitting on the login screen already downloads the full dashboard bundle (all sections, Framer Motion, the mock layer). Low urgency at today's bundle size, but the fix (`React.lazy` per route) is cheap and compounds in value as the app grows.

### Folder structure
Mostly consistent: domain-flat `components/{common,dashboard,layout,ui}`, isolated `charts/`, `hooks/`, `mock/`, `types/`. One inconsistency worth a deliberate decision rather than leaving implicit: the dashboard route lives in `pages/DashboardPage.tsx` while the login route lives in `features/login/LoginPage.tsx` — two different organizing conventions for what are both route-level pages. This was intentional early on (login was built to stay decoupled, "connect later"); now that both routes and the connection point (`App.tsx`) are stable, it's worth either moving both into `pages/` or promoting the dashboard into a `features/dashboard/` to match — cosmetic, but worth resolving before more route-level pages are added.

### Scalability
The UI/component layer scales fine — it's the **data layer's assumptions** that don't yet: every mock getter (`getProcesses()`, `getLogEntries()`, `getAlerts()`) returns its full, small, fixed-size mock array with no limit/offset/date-range parameters, and `TopProcessesSection`/`LogsSection` render their lists with a plain `.map()` and no virtualization. A live agent easily reports hundreds of processes or a fast-scrolling log stream; neither section would degrade gracefully today. The whole architecture is also implicitly single-host — `getHostInfo()`, `getSystemHealth()`, and the one `useLiveMetrics()` call in `DashboardPage` assume exactly one server. If multi-host is on the roadmap at all, threading a `hostId` through the mock/data layer now (even as an ignored parameter) is far cheaper than retrofitting it later.

### Component architecture
The strongest part of the codebase. Every dashboard section is presentational and takes its data as an optional prop defaulting to a mock getter, so components are independently usable/testable and the "swap the data source" story is real, not aspirational. `DashboardPage` is the single place that turns a live data hook into props for two children (`MetricCardGrid`, `LiveMonitoringSection`) — exactly the shape you want when that hook becomes a real WebSocket subscription later, so only one call site changes. Reusable primitives (`SectionCard`, `Chip`, `IconTile`, `EmptyState`, `FilterChipRow` + `useCategoryFilter`) eliminated the repeated-markup problems that existed a few passes ago.

### Design system
Token layer is complete and self-documenting (colors, type scale, radius, spacing, shadow all live in one file with rationale comments). Variant components (`Button`, `Badge`, `IconTile`) use `class-variance-authority` consistently. No Storybook or isolated component-preview environment exists — for a design system that's explicitly meant to be reused, that's a reasonable next investment once the component count grows past what a single dashboard page can showcase.

### Accessibility
Better than most v0.1 dashboards: decorative icons/SVGs are `aria-hidden`, icon-only buttons carry `aria-label`, the chart has a `role="img"` with a live text description, tables use `<caption className="sr-only">` and `scope="col"`, custom motion respects `prefers-reduced-motion` via `MotionConfig`, disclosure controls now correctly pair `aria-expanded` with `aria-controls`. Not yet verified: keyboard-only walkthroughs of the full app, and no automated a11y checks (axe/lighthouse-ci) run in CI — because there is no CI yet (see Code quality).

### Code quality
TypeScript strict mode, zero `tsc`/`eslint` errors, consistent naming, no dead exports found in this pass. Two real gaps for a release review to name plainly:
- **Zero automated tests.** No unit tests, no component tests, no e2e — nothing in the repo currently prevents a regression from shipping silently. This is the single most important gap to close before backend integration adds a whole new failure surface (network errors, race conditions, stale data) that manual testing won't reliably catch.
- **No error boundary anywhere.** An uncaught render error in any one section currently white-screens the entire app with no fallback UI — acceptable at zero-risk with static mock data, not acceptable once a section can throw on a malformed API response.

### Performance
Recharts is already isolated into its own lazy-loaded chunk (`~394KB / 108KB gzip`) so it only loads when Live Monitoring actually mounts. Main bundle is `~465KB / 147KB gzip` — reasonable today. `React.memo` now prevents the 7 static dashboard sections from re-rendering on every one-second live-metric tick (this pass). Two lower-priority items: Inter is loaded from Google's font CDN with no self-hosted fallback (an external dependency and a minor privacy/CSP consideration), and route-level code-splitting hasn't been done yet (see Routing).

### Future backend integration — readiness
The mock layer's "swap sync for async, keep the same function name/shape" story (documented above) holds for the **data-fetching functions themselves**, but not for free — the component-side wiring (`metrics = getMetricCards()` as a default parameter) cannot await a promise, so every call site will need real `useState`/`useEffect` (or a data-fetching library) for loading/error/success states that don't exist anywhere in the UI today. There is also no environment configuration (no `.env`, no `VITE_API_BASE_URL`) and no API client module — every future `fetch` call currently has nowhere established to live.

### Predicted integration issues

**FastAPI**
- No API client abstraction exists yet — base URL, headers, and error handling would otherwise get reinvented per mock file. Build one seam now, even unused, so the async migration touches one file instead of nine.
- No dev-time CORS/proxy setup (`vite.config.ts` has no `server.proxy`) — expect a CORS error on the first real request unless FastAPI's `CORSMiddleware` or a Vite proxy is configured up front.
- The default-prop data pattern (`data = getX()`) silently breaks once `getX` becomes `async` — components need an actual fetch lifecycle (loading/error states), which is new code, not a signature change.

**WebSockets**
- This is the biggest architectural mismatch to plan for. `useLiveMetrics`'s `LiveDataSource` interface is **pull-shaped** (`getNextValue(metric, previousValue)`, called on a client-side `setInterval`) — a good fit for the mock random-walk generator, but a WebSocket is **push-shaped** (the server sends messages whenever it wants, not on the client's schedule). Swapping the `source` prop won't be enough; the hook's internal `setInterval` loop needs to become a `ws.onmessage` subscription, which is a real (if contained) rewrite of `useLiveMetrics`, not a drop-in.
- No reconnect/backoff/heartbeat handling exists anywhere, and no UI state currently reflects "connecting" / "reconnecting" / "disconnected" — the `ConnectionStatus` type already has room for `degraded`/`disconnected`, but nothing drives those values today. Design the reconnect UX before writing the WS client, not after.
- The current architecture's one real strength here: `DashboardPage` already owns the single live-data subscription and passes it down as props to two children — keep that shape. If `MetricCardGrid` and `LiveMonitoringSection` each opened their own WebSocket independently, you'd get duplicate connections.
- `TimeSeriesPoint.time` is stored as an already-formatted display string (`"14:32:07"`), not a raw timestamp. A real backend will more likely send epoch millis or ISO-8601; formatting should happen at render time, not be baked into the stored series, or the chart's `dataKey="time"` wiring needs to change alongside the data source.

**Linux Agent**
- Process/log volume from a real agent is unbounded; `TopProcessesSection` and `LogsSection` currently render small fixed mock arrays with a plain `.map()` and no virtualization or pagination. Decide the query contract (top-N + sort, or full list + client virtualization) before the agent starts sending real volumes.
- Nothing today models agent staleness/heartbeat — `lastSyncedAt`/`latencyMs` are static display fields, not derived from an actual liveness check. Decide the "agent hasn't reported in N seconds" UX now; it touches the same Header/StatusIndicator components the WebSocket reconnect UX will need.
- The architecture is implicitly single-agent/single-host (see Scalability) — confirm that's intentional for this release, or thread a host identifier through the data layer before, not after, the agent exists.

**SQLite**
- Frontend-facing implications are really the same pagination/query-shape gap called out above (Logs/Alerts/Analytics history) — SQLite itself is invisible to the frontend, but "return everything, unfiltered" won't survive contact with a real, growing table.
- **Analytics has no real data contract at all** — `AnalyticsPanel { id, label }` is placeholder metadata for two empty tiles, not a chart spec. This is the one section where "point it at the database" requires a design decision (what's queried, what chart type, what time range) that hasn't been made yet, not just a wiring change.

### Recommended improvements before backend development begins

1. **Add a test harness** (Vitest + React Testing Library at minimum) and cover the data-layer contracts (`useCategoryFilter`, `useLiveMetrics`, the mock getters) — the highest-leverage gap, and cheapest to close now versus after the API surface grows.
2. **Introduce an API client seam** (`src/lib/apiClient.ts` or similar) and `.env`-based `VITE_API_BASE_URL`, even before any real endpoint exists, so the async migration has one place to land instead of nine.
3. **Add a top-level error boundary** around the routed app so a future fetch/render failure degrades to a fallback screen instead of a white screen.
4. **Redesign `useLiveMetrics` around a push model** (subscription/callback shape) before writing the WebSocket client — the current pull/interval shape is right for the mock, wrong for the real thing.
5. **Model connection state for real** — decide what `ConnectionStatus`'s `degraded`/`disconnected` states look like in the UI now, since both the WebSocket reconnect flow and Linux Agent staleness will need the same states.
6. **Give Analytics a real data contract** (what's queried, what's charted) before backend work targets it, so it isn't designed reactively.
7. **Decide single-host vs. multi-host** deliberately, and thread a host identifier through the data layer now if multi-host is ever in scope.
8. Lower priority: route-level code-splitting (`React.lazy` for `LoginPage`/`DashboardPage`), self-host the Inter font, resolve the `pages/` vs. `features/login` structural inconsistency.
