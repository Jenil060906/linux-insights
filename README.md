# Linux Insight

Intelligent Linux Observability Platform — a dark-theme monitoring dashboard for Linux servers.

This repo is a monorepo laid out for the full product (agent → API → dashboard), but **only the `frontend/` is implemented so far**. Everything else is a reserved, empty scaffold for later phases. The frontend currently runs entirely on a mock data layer — there is no backend, no agent, and no real authentication yet.

## Repository layout

| Directory | Status | Purpose |
|---|---|---|
| `frontend/` | **Implemented** | React dashboard UI — see below |
| `backend/` | Scaffold only | Future API server (`app`, `api`, `database`, `models`, `services`, `websocket`) |
| `linux-agent/` | Scaffold only | Future host-side metrics collector |
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
