import { memo } from "react";
import { BarChart3 } from "lucide-react";
import { SectionCard } from "@/components/common/SectionCard";
import { PlaceholderCard } from "@/components/common/PlaceholderCard";
import { getAnalyticsPanels } from "@/mock/analytics";
import type { AnalyticsPanel } from "@/types/system";

interface AnalyticsSectionProps {
  panels?: AnalyticsPanel[];
}

// Historical analytics & trend breakdowns — charting is introduced in a later phase.
// Presentational — panel list flows in via props. Memoized: gets no props
// from DashboardPage, so it's excluded from the once-a-second re-render the
// live metric tick otherwise triggers.
export const AnalyticsSection = memo(function AnalyticsSection({
  panels = getAnalyticsPanels(),
}: AnalyticsSectionProps) {
  return (
    <SectionCard title="Analytics" description="Historical trends & breakdowns" icon={BarChart3}>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        {panels.map((panel) => (
          <PlaceholderCard key={panel.id} icon={BarChart3} label={panel.label} />
        ))}
      </div>
    </SectionCard>
  );
});
