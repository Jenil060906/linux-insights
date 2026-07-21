// Mock data layer — live-monitoring data source.
//
// This is the one seam a real backend integration touches. `mockLiveDataSource`
// implements the `LiveDataSource` interface below by random-walking numbers on
// a client-side timer. A future WebSocket/SSE/polling client implements the
// exact same interface (`getNextValue`), so `useLiveMetrics` — and every
// component downstream of it — needs zero changes when the mock is swapped out.
import type { MetricKey } from "@/types/system";

export interface LiveDataSource {
  getNextValue(metric: MetricKey, previousValue: number): number;
}

interface MetricRange {
  min: number;
  max: number;
  /** Max absolute change allowed per tick — keeps the walk visually smooth. */
  volatility: number;
  /** Decimal places to round generated values to. */
  precision: number;
}

export const METRIC_RANGES: Record<MetricKey, MetricRange> = {
  cpu: { min: 4, max: 96, volatility: 7, precision: 0 },
  ram: { min: 25, max: 92, volatility: 2.5, precision: 0 },
  disk: { min: 15, max: 97, volatility: 0.6, precision: 0 },
  network: { min: 0.1, max: 9, volatility: 0.9, precision: 1 },
};

function round(value: number, precision: number): number {
  const factor = 10 ** precision;
  return Math.round(value * factor) / factor;
}

// Bounded random walk: each new value is a small step from the previous one
// (clamped to a realistic range), so the series drifts naturally instead of
// jumping between unrelated numbers every tick.
function randomWalk(previousValue: number, range: MetricRange): number {
  const delta = (Math.random() - 0.5) * 2 * range.volatility;
  const next = Math.min(range.max, Math.max(range.min, previousValue + delta));
  return round(next, range.precision);
}

export const mockLiveDataSource: LiveDataSource = {
  getNextValue(metric, previousValue) {
    return randomWalk(previousValue, METRIC_RANGES[metric]);
  },
};
