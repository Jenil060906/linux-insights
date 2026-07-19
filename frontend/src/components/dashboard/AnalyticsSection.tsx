import { BarChart3 } from "lucide-react";
import { SectionCard } from "@/components/common/SectionCard";
import { PlaceholderCard } from "@/components/common/PlaceholderCard";

// Historical analytics & trend breakdowns — charting is introduced in a later phase.
export function AnalyticsSection() {
  return (
    <SectionCard title="Analytics" description="Historical trends & breakdowns" icon={BarChart3}>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <PlaceholderCard icon={BarChart3} label="Resource trend chart" />
        <PlaceholderCard icon={BarChart3} label="Usage breakdown chart" />
      </div>
    </SectionCard>
  );
}
