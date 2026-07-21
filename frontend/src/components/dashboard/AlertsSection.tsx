import { memo } from "react";
import { AlertTriangle, CheckCircle2, Info, ListFilter, OctagonAlert, type LucideIcon } from "lucide-react";
import { SectionCard } from "@/components/common/SectionCard";
import { FilterChipRow, type FilterOption } from "@/components/common/FilterChipRow";
import { EmptyState } from "@/components/common/EmptyState";
import { Badge } from "@/components/ui/badge";
import { useCategoryFilter, type CategoryFilter } from "@/hooks/useCategoryFilter";
import { cn } from "@/lib/utils";
import { getAlerts } from "@/mock/alerts";
import type { AlertItem, AlertSeverity } from "@/types/system";

const SEVERITY_CONFIG: Record<
  AlertSeverity,
  {
    icon: LucideIcon;
    badgeVariant: "danger" | "warning" | "primary";
    label: string;
    iconClassName: string;
  }
> = {
  critical: { icon: OctagonAlert, badgeVariant: "danger", label: "Critical", iconClassName: "text-danger" },
  warning: { icon: AlertTriangle, badgeVariant: "warning", label: "Warning", iconClassName: "text-warning" },
  info: { icon: Info, badgeVariant: "primary", label: "Info", iconClassName: "text-primary" },
};

const ALERT_SEVERITIES: AlertSeverity[] = ["critical", "warning", "info"];
const getAlertSeverity = (alert: AlertItem) => alert.severity;

const FILTER_OPTIONS: FilterOption<CategoryFilter<AlertSeverity>>[] = [
  { key: "all", label: "All", icon: ListFilter },
  { key: "critical", label: "Critical", icon: SEVERITY_CONFIG.critical.icon },
  { key: "warning", label: "Warning", icon: SEVERITY_CONFIG.warning.icon },
  { key: "info", label: "Info", icon: SEVERITY_CONFIG.info.icon },
];

interface AlertsSectionProps {
  alerts?: AlertItem[];
}

// Recent alerts feed with client-side severity filtering. Presentational —
// data flows in via props. Memoized: with no props passed by DashboardPage,
// it would otherwise re-render every second alongside the live metric tick
// for no reason.
export const AlertsSection = memo(function AlertsSection({ alerts = getAlerts() }: AlertsSectionProps) {
  const {
    filter,
    setFilter,
    counts,
    visibleItems: visibleAlerts,
  } = useCategoryFilter(alerts, getAlertSeverity, ALERT_SEVERITIES);

  return (
    <SectionCard title="Alerts" description="Recent system alerts" icon={AlertTriangle}>
      <FilterChipRow
        groupLabel="Filter alerts by severity"
        options={FILTER_OPTIONS}
        active={filter}
        counts={counts}
        onChange={setFilter}
      />

      {visibleAlerts.length === 0 ? (
        <EmptyState icon={CheckCircle2} message="No alerts in this category." />
      ) : (
        <div className="flex flex-col gap-2">
          {visibleAlerts.map((alert) => {
            const config = SEVERITY_CONFIG[alert.severity];
            const Icon = config.icon;
            return (
              <div
                key={alert.id}
                className="flex items-start gap-3 rounded-md border border-border bg-surface/50 px-3 py-2.5 transition-colors hover:bg-surface/80"
              >
                <Icon aria-hidden="true" className={cn("mt-0.5 h-4 w-4 shrink-0", config.iconClassName)} />
                <div className="flex-1 min-w-0">
                  <p className="truncate text-sm text-foreground">{alert.title}</p>
                  <p className="text-2xs text-muted-foreground">
                    {alert.source} · {alert.timestamp}
                  </p>
                </div>
                <Badge variant={config.badgeVariant}>{config.label}</Badge>
              </div>
            );
          })}
        </div>
      )}
    </SectionCard>
  );
});
