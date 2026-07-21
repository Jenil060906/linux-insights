import { useEffect, useRef, useState } from "react";
import { mockLiveDataSource, type LiveDataSource } from "@/mock/liveDataSource";
import { getLiveMonitoringSeries } from "@/mock/metrics";
import type { MetricKey, TimeSeriesPoint } from "@/types/system";

const METRIC_KEYS: MetricKey[] = ["cpu", "ram", "disk", "network"];

function formatClock(date: Date): string {
  return date.toLocaleTimeString("en-US", {
    hour12: false,
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

// Seeds a full rolling window ending "now" from the last known mock value per
// metric, so the chart opens already full instead of growing from one point.
function buildInitialSeries(
  source: LiveDataSource,
  windowSize: number,
  intervalMs: number
): Record<MetricKey, TimeSeriesPoint[]> {
  const seed = getLiveMonitoringSeries();
  const now = Date.now();
  const result = {} as Record<MetricKey, TimeSeriesPoint[]>;

  for (const key of METRIC_KEYS) {
    const points: TimeSeriesPoint[] = [];
    let value = seed[key][seed[key].length - 1]?.value ?? 0;
    for (let i = windowSize - 1; i >= 0; i--) {
      value = source.getNextValue(key, value);
      points.push({ time: formatClock(new Date(now - i * intervalMs)), value });
    }
    result[key] = points;
  }
  return result;
}

interface UseLiveMetricsOptions {
  /** Tick frequency in ms. Defaults to 1000 — one new sample per second. */
  intervalMs?: number;
  /** Rolling window length kept per metric. */
  windowSize?: number;
  /** Swap point for a real backend: any object implementing `getNextValue`. */
  source?: LiveDataSource;
  /** Set to false to freeze the series (e.g. in tests). */
  live?: boolean;
}

// Simulates a live telemetry stream: one new randomly-generated sample per
// metric every `intervalMs`, appended to a fixed-size rolling window.
//
// This hook is the ONLY place that knows *how* new values arrive. Today that's
// `mockLiveDataSource`'s client-side random walk; later it's a WebSocket
// message handler or a REST poll fed through the same `LiveDataSource`
// interface. Either way, the return shape (`Record<MetricKey, TimeSeriesPoint[]>`)
// and every component consuming this hook stay exactly the same.
export function useLiveMetrics({
  intervalMs = 1000,
  windowSize = 60,
  source = mockLiveDataSource,
  live = true,
}: UseLiveMetricsOptions = {}): Record<MetricKey, TimeSeriesPoint[]> {
  const [series, setSeries] = useState(() => buildInitialSeries(source, windowSize, intervalMs));
  const sourceRef = useRef(source);
  sourceRef.current = source;

  useEffect(() => {
    if (!live) return;

    const id = window.setInterval(() => {
      setSeries((prev) => {
        const next = {} as Record<MetricKey, TimeSeriesPoint[]>;
        const time = formatClock(new Date());
        for (const key of METRIC_KEYS) {
          const previousValue = prev[key][prev[key].length - 1]?.value ?? 0;
          const value = sourceRef.current.getNextValue(key, previousValue);
          const updated = [...prev[key], { time, value }];
          next[key] = updated.length > windowSize ? updated.slice(updated.length - windowSize) : updated;
        }
        return next;
      });
    }, intervalMs);

    return () => window.clearInterval(id);
  }, [intervalMs, windowSize, live]);

  return series;
}
