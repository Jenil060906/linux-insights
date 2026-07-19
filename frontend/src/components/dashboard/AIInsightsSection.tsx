import { Gauge, PiggyBank, ServerCog, ShieldAlert, Sparkles, type LucideIcon } from "lucide-react";
import { SectionCard } from "@/components/common/SectionCard";
import { Badge } from "@/components/ui/badge";
import { aiInsights as defaultAiInsights } from "@/data/placeholder";
import type { AIInsight, InsightCategory, InsightImpact } from "@/types/system";

const CATEGORY_CONFIG: Record<InsightCategory, { icon: LucideIcon; label: string }> = {
  performance: { icon: Gauge, label: "Performance" },
  security: { icon: ShieldAlert, label: "Security" },
  cost: { icon: PiggyBank, label: "Cost" },
  reliability: { icon: ServerCog, label: "Reliability" },
};

const IMPACT_BADGE: Record<InsightImpact, { variant: "outline" | "warning" | "danger"; label: string }> = {
  low: { variant: "outline", label: "Low impact" },
  medium: { variant: "warning", label: "Medium impact" },
  high: { variant: "danger", label: "High impact" },
};

interface AIInsightsSectionProps {
  insights?: AIInsight[];
}

// AI-generated insight feed. Presentational — data flows in via props.
export function AIInsightsSection({ insights = defaultAiInsights }: AIInsightsSectionProps) {
  return (
    <SectionCard
      title="AI Insights"
      description="Anomaly detection & recommendations"
      icon={Sparkles}
    >
      <div className="flex flex-col gap-2">
        {insights.map((insight) => {
          const category = CATEGORY_CONFIG[insight.category];
          const impact = IMPACT_BADGE[insight.impact];
          const CategoryIcon = category.icon;
          return (
            <div
              key={insight.id}
              className="flex items-start gap-3 rounded-md border border-border bg-surface/50 px-3 py-2.5 transition-colors hover:bg-surface/80"
            >
              <div className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-sm border border-border bg-surface text-primary">
                <CategoryIcon aria-hidden="true" className="h-3.5 w-3.5" />
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <p className="text-sm font-medium text-foreground">{insight.title}</p>
                  <Badge variant={impact.variant}>{impact.label}</Badge>
                </div>
                <p className="mt-1 text-xs text-muted-foreground">{insight.description}</p>
                <p className="mt-1.5 text-2xs text-muted-foreground">
                  {category.label} · {insight.timestamp}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </SectionCard>
  );
}
