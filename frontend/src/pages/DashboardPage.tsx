import { SystemHealthHero } from "@/components/dashboard/SystemHealthHero";
import { MetricCardGrid } from "@/components/dashboard/MetricCardGrid";
import { LiveMonitoringSection } from "@/components/dashboard/LiveMonitoringSection";
import { AIInsightsSection } from "@/components/dashboard/AIInsightsSection";
import { AlertsSection } from "@/components/dashboard/AlertsSection";
import { TopProcessesSection } from "@/components/dashboard/TopProcessesSection";
import { AnalyticsSection } from "@/components/dashboard/AnalyticsSection";
import { QuickActionsSection } from "@/components/dashboard/QuickActionsSection";
import { LogsSection } from "@/components/dashboard/LogsSection";
import { FadeIn } from "@/components/common/FadeIn";

// Phase 1 dashboard composition — layout + static placeholder sections only.
// Kept separate from App.tsx so routing can be introduced later without reshuffling.
export function DashboardPage() {
  return (
    <>
      <FadeIn>
        <SystemHealthHero />
      </FadeIn>

      <FadeIn delay={0.05}>
        <MetricCardGrid />
      </FadeIn>

      <FadeIn delay={0.1}>
        <LiveMonitoringSection />
      </FadeIn>

      <FadeIn delay={0.15}>
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <AIInsightsSection />
          <AlertsSection />
        </div>
      </FadeIn>

      <FadeIn delay={0.2}>
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <TopProcessesSection />
          <QuickActionsSection />
        </div>
      </FadeIn>

      <FadeIn delay={0.25}>
        <AnalyticsSection />
      </FadeIn>

      <FadeIn delay={0.3}>
        <LogsSection />
      </FadeIn>
    </>
  );
}
