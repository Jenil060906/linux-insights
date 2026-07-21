import { MetricCard } from "@/components/dashboard/MetricCard";
import { getMetricCards } from "@/mock/metrics";
import type { MetricCardData } from "@/types/system";

interface MetricCardGridProps {
  metrics?: MetricCardData[];
}

// Responsive grid of the four core resource metrics: CPU, RAM, Disk, Network.
// 4-up from lg (1024px) — laptop widths have room for all four; only phone
// and tablet (below lg) fall back to 2-up. Desktop/large screens (already
// >=1024) render identically to before, just via an earlier-firing breakpoint.
export function MetricCardGrid({ metrics = getMetricCards() }: MetricCardGridProps) {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {metrics.map((metric) => (
        <MetricCard key={metric.id} data={metric} />
      ))}
    </div>
  );
}
