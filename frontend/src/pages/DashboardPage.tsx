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
import { useLiveMetrics } from "@/hooks/useLiveMetrics";
import { buildLiveMetricCards } from "@/mock/metrics";

// Phase 1 dashboard composition — layout + placeholder sections. Data is
// still 100% mock, but Metric Cards and Live Monitoring are wired to a
// simulated live stream (see useLiveMetrics) rather than a static snapshot.
//
// This is the single place that "goes live": both sections stay presentational
// (they accept series/metrics as props with static-mock defaults, so they're
// still usable standalone). When a real backend arrives, only the data source
// passed to `useLiveMetrics` changes — every component below stays the same.
export function DashboardPage() {
  const liveSeries = useLiveMetrics();
  const liveMetricCards = buildLiveMetricCards(liveSeries);

  return (
    <>
      <FadeIn>
        <SystemHealthHero />
      </FadeIn>

      <FadeIn delay={0.05}>
        <MetricCardGrid metrics={liveMetricCards} />
      </FadeIn>

      <FadeIn delay={0.1}>
        <LiveMonitoringSection series={liveSeries} />
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
