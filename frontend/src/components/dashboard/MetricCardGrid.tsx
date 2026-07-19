import { MetricCard } from "@/components/dashboard/MetricCard";
import { metricCards as defaultMetricCards } from "@/data/placeholder";
import type { MetricCardData } from "@/types/system";

interface MetricCardGridProps {
  metrics?: MetricCardData[];
}

// Responsive grid of the four core resource metrics: CPU, RAM, Disk, Network.
export function MetricCardGrid({ metrics = defaultMetricCards }: MetricCardGridProps) {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
      {metrics.map((metric) => (
        <MetricCard key={metric.id} data={metric} />
      ))}
    </div>
  );
}
