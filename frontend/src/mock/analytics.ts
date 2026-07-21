// Mock data layer — "analytics" domain. See server.ts for the function-vs-constant rationale.
//
// Analytics has no real chart data yet (see AnalyticsSection — charting for
// this section is a later phase), so this is metadata for the placeholder
// panels rather than a data series. Still lives here, not in the component,
// so the panel list is swappable without touching AnalyticsSection.
import type { AnalyticsPanel } from "@/types/system";

const analyticsPanels: AnalyticsPanel[] = [
  { id: "resource-trend", label: "Resource trend chart" },
  { id: "usage-breakdown", label: "Usage breakdown chart" },
];

/** Mirrors GET /api/analytics */
export function getAnalyticsPanels(): AnalyticsPanel[] {
  return analyticsPanels;
}
