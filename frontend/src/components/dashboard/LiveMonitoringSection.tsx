import { lazy, Suspense, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Activity, Cpu, HardDrive, MemoryStick, Wifi, type LucideIcon } from "lucide-react";
import { SectionCard } from "@/components/common/SectionCard";
import { Chip } from "@/components/common/Chip";
import { Badge } from "@/components/ui/badge";
import { ChartSkeleton } from "@/charts/ChartSkeleton";
import { chartTheme } from "@/charts/theme";
import { getLiveMonitoringSeries } from "@/mock/metrics";
import type { MetricKey, TimeSeriesPoint } from "@/types/system";

// Recharts (+ d3 deps) is the heaviest dependency in the app — split it into its
// own chunk so it only loads for the one section that needs it.
const UsageAreaChart = lazy(() =>
  import("@/charts/UsageAreaChart").then((m) => ({ default: m.UsageAreaChart }))
);

interface MetricTab {
  key: MetricKey;
  label: string;
  icon: LucideIcon;
  unit: string;
}

const METRIC_TABS: MetricTab[] = [
  { key: "cpu", label: "CPU", icon: Cpu, unit: "%" },
  { key: "ram", label: "Memory", icon: MemoryStick, unit: "%" },
  { key: "disk", label: "Disk", icon: HardDrive, unit: "%" },
  { key: "network", label: "Network", icon: Wifi, unit: " MB/s" },
];

interface LiveMonitoringSectionProps {
  series?: Record<MetricKey, TimeSeriesPoint[]>;
}

// Single-series usage chart, switchable by metric. `series` defaults to a
// static mock snapshot for standalone use; on the dashboard it's fed a
// live-ticking series from useLiveMetrics (see DashboardPage) — this
// component doesn't know or care whether its data is static or live.
export function LiveMonitoringSection({ series = getLiveMonitoringSeries() }: LiveMonitoringSectionProps) {
  const [active, setActive] = useState<MetricKey>("cpu");
  const activeTab = METRIC_TABS.find((tab) => tab.key === active)!;
  const activeData = series[active];
  const latest = activeData[activeData.length - 1]?.value;

  return (
    <SectionCard
      title="Live Monitoring"
      description="Real-time resource activity"
      icon={Activity}
      action={
        <Badge variant="success">
          <span
            className="h-1.5 w-1.5 rounded-full bg-success motion-safe:animate-pulse-dot"
            aria-hidden="true"
          />
          Live
        </Badge>
      }
    >
      <div role="group" aria-label="Select metric to display" className="mb-4 flex flex-wrap gap-1.5">
        {METRIC_TABS.map((tab) => (
          <Chip
            key={tab.key}
            icon={tab.icon}
            active={tab.key === active}
            onClick={() => setActive(tab.key)}
          >
            {tab.label}
          </Chip>
        ))}
      </div>

      <div
        role="img"
        aria-label={`${activeTab.label} usage, currently ${latest}${activeTab.unit.trim()}, updating live`}
      >
        {/* Keyed on the selected tab (not on data ticks) so switching metrics
            crossfades, while per-second data updates animate inside Recharts. */}
        <AnimatePresence mode="wait">
          <motion.div
            key={active}
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -6 }}
            transition={{ duration: 0.2, ease: "easeOut" }}
          >
            <Suspense fallback={<ChartSkeleton height={220} />}>
              <UsageAreaChart data={activeData} unit={activeTab.unit} color={chartTheme.primary} />
            </Suspense>
          </motion.div>
        </AnimatePresence>
      </div>
    </SectionCard>
  );
}
