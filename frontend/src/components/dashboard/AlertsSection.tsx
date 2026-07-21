import { useMemo, useState } from "react";
import { AlertTriangle, Info, ListFilter, OctagonAlert, type LucideIcon } from "lucide-react";
import { SectionCard } from "@/components/common/SectionCard";
import { Chip } from "@/components/common/Chip";
import { Badge } from "@/components/ui/badge";
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

type SeverityFilter = "all" | AlertSeverity;

interface AlertsSectionProps {
  alerts?: AlertItem[];
}

// Recent alerts feed with client-side severity filtering. Presentational — data flows in via props.
export function AlertsSection({ alerts = getAlerts() }: AlertsSectionProps) {
  const [filter, setFilter] = useState<SeverityFilter>("all");

  const counts = useMemo(() => {
    return alerts.reduce<Record<SeverityFilter, number>>(
      (acc, alert) => {
        acc.all += 1;
        acc[alert.severity] += 1;
        return acc;
      },
      { all: 0, critical: 0, warning: 0, info: 0 }
    );
  }, [alerts]);

  const visibleAlerts = filter === "all" ? alerts : alerts.filter((alert) => alert.severity === filter);

  const filters: { key: SeverityFilter; label: string; icon?: LucideIcon }[] = [
    { key: "all", label: "All", icon: ListFilter },
    { key: "critical", label: "Critical", icon: SEVERITY_CONFIG.critical.icon },
    { key: "warning", label: "Warning", icon: SEVERITY_CONFIG.warning.icon },
    { key: "info", label: "Info", icon: SEVERITY_CONFIG.info.icon },
  ];

  return (
    <SectionCard title="Alerts" description="Recent system alerts" icon={AlertTriangle}>
      <div role="group" aria-label="Filter alerts by severity" className="mb-4 flex flex-wrap gap-1.5">
        {filters.map((item) => (
          <Chip
            key={item.key}
            icon={item.icon}
            active={filter === item.key}
            count={counts[item.key]}
            onClick={() => setFilter(item.key)}
          >
            {item.label}
          </Chip>
        ))}
      </div>

      {visibleAlerts.length === 0 ? (
        <p className="rounded-md border border-dashed border-border bg-surface/40 px-3 py-6 text-center text-xs text-muted-foreground">
          No alerts in this category.
        </p>
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
}
