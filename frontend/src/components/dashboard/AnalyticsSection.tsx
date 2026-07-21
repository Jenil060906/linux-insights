import { BarChart3 } from "lucide-react";
import { SectionCard } from "@/components/common/SectionCard";
import { PlaceholderCard } from "@/components/common/PlaceholderCard";
import { getAnalyticsPanels } from "@/mock/analytics";
import type { AnalyticsPanel } from "@/types/system";

interface AnalyticsSectionProps {
  panels?: AnalyticsPanel[];
}

// Historical analytics & trend breakdowns — charting is introduced in a later phase.
// Presentational — panel list flows in via props.
export function AnalyticsSection({ panels = getAnalyticsPanels() }: AnalyticsSectionProps) {
  return (
    <SectionCard title="Analytics" description="Historical trends & breakdowns" icon={BarChart3}>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        {panels.map((panel) => (
          <PlaceholderCard key={panel.id} icon={BarChart3} label={panel.label} />
        ))}
      </div>
    </SectionCard>
  );
}
