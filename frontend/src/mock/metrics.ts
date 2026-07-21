// Mock data layer — "metrics" domain (resource cards + live monitoring series).
// See server.ts for the function-vs-constant rationale — same pattern here.
import { Cpu, HardDrive, MemoryStick, Wifi } from "lucide-react";
import type { MetricCardData, MetricKey, TimeSeriesPoint } from "@/types/system";

const metricCards: MetricCardData[] = [
  {
    id: "cpu",
    label: "CPU Usage",
    value: "42",
    unit: "%",
    trend: "up",
    trendValue: "+3.2%",
    sparkline: [30, 34, 32, 38, 36, 40, 42],
    icon: Cpu,
  },
  {
    id: "ram",
    label: "Memory Usage",
    value: "6.8",
    unit: "GB / 16GB",
    trend: "flat",
    trendValue: "+0.1%",
    sparkline: [40, 42, 41, 43, 42, 42, 43],
    icon: MemoryStick,
  },
  {
    id: "disk",
    label: "Disk Usage",
    value: "218",
    unit: "GB / 512GB",
    trend: "up",
    trendValue: "+0.8%",
    sparkline: [38, 39, 39, 40, 41, 41, 42],
    icon: HardDrive,
  },
  {
    id: "network",
    label: "Network I/O",
    value: "1.4",
    unit: "MB/s",
    trend: "down",
    trendValue: "-5.4%",
    sparkline: [22, 26, 24, 20, 18, 16, 15],
    icon: Wifi,
  },
];

// 60 minutes of 5-minute-interval samples per metric — static, for the Live Monitoring chart.
const liveMonitoringSeries: Record<MetricKey, TimeSeriesPoint[]> = {
  cpu: [
    { time: "13:35", value: 31 },
    { time: "13:40", value: 34 },
    { time: "13:45", value: 29 },
    { time: "13:50", value: 38 },
    { time: "13:55", value: 44 },
    { time: "14:00", value: 40 },
    { time: "14:05", value: 36 },
    { time: "14:10", value: 41 },
    { time: "14:15", value: 47 },
    { time: "14:20", value: 39 },
    { time: "14:25", value: 43 },
    { time: "14:30", value: 42 },
  ],
  ram: [
    { time: "13:35", value: 39 },
    { time: "13:40", value: 40 },
    { time: "13:45", value: 40 },
    { time: "13:50", value: 41 },
    { time: "13:55", value: 42 },
    { time: "14:00", value: 41 },
    { time: "14:05", value: 42 },
    { time: "14:10", value: 43 },
    { time: "14:15", value: 43 },
    { time: "14:20", value: 42 },
    { time: "14:25", value: 43 },
    { time: "14:30", value: 43 },
  ],
  disk: [
    { time: "13:35", value: 40 },
    { time: "13:40", value: 40 },
    { time: "13:45", value: 40 },
    { time: "13:50", value: 41 },
    { time: "13:55", value: 41 },
    { time: "14:00", value: 41 },
    { time: "14:05", value: 41 },
    { time: "14:10", value: 42 },
    { time: "14:15", value: 42 },
    { time: "14:20", value: 42 },
    { time: "14:25", value: 42 },
    { time: "14:30", value: 43 },
  ],
  network: [
    { time: "13:35", value: 0.9 },
    { time: "13:40", value: 1.3 },
    { time: "13:45", value: 1.1 },
    { time: "13:50", value: 1.8 },
    { time: "13:55", value: 2.1 },
    { time: "14:00", value: 1.6 },
    { time: "14:05", value: 1.2 },
    { time: "14:10", value: 1.5 },
    { time: "14:15", value: 1.9 },
    { time: "14:20", value: 1.3 },
    { time: "14:25", value: 1.1 },
    { time: "14:30", value: 1.4 },
  ],
};

/** Mirrors GET /api/metrics */
export function getMetricCards(): MetricCardData[] {
  return metricCards;
}

/** Mirrors GET /api/metrics/series */
export function getLiveMonitoringSeries(): Record<MetricKey, TimeSeriesPoint[]> {
  return liveMonitoringSeries;
}

// How each metric's raw series value (a plain number — a 0-100 usage percent
// for cpu/ram/disk, MB/s for network) becomes the string shown on its card.
const METRIC_DISPLAY: Record<MetricKey, { toDisplayValue: (raw: number) => string; unit: string }> = {
  cpu: { toDisplayValue: (v) => `${Math.round(v)}`, unit: "%" },
  ram: { toDisplayValue: (v) => ((v / 100) * 16).toFixed(1), unit: "GB / 16GB" },
  disk: { toDisplayValue: (v) => `${Math.round((v / 100) * 512)}`, unit: "GB / 512GB" },
  network: { toDisplayValue: (v) => v.toFixed(1), unit: "MB/s" },
};

/**
 * Derives display-ready metric cards (value, trend, sparkline) from a live
 * time series produced by `useLiveMetrics`. Static metadata — id, label,
 * icon — still comes from `metricCards` above; only the numbers are
 * recomputed on every tick. Kept alongside `getMetricCards` since both read
 * from the same static metric metadata.
 */
export function buildLiveMetricCards(series: Record<MetricKey, TimeSeriesPoint[]>): MetricCardData[] {
  return metricCards.map((card) => {
    const key = card.id as MetricKey;
    const points = series[key];
    const latest = points[points.length - 1]?.value ?? 0;
    const previous = points[points.length - 2]?.value ?? latest;
    const pctChange = previous === 0 ? 0 : ((latest - previous) / previous) * 100;
    const display = METRIC_DISPLAY[key];

    return {
      ...card,
      value: display.toDisplayValue(latest),
      unit: display.unit,
      trend: Math.abs(pctChange) < 0.3 ? "flat" : pctChange > 0 ? "up" : "down",
      trendValue: `${pctChange >= 0 ? "+" : ""}${pctChange.toFixed(1)}%`,
      sparkline: points.map((p) => p.value),
    };
  });
}
