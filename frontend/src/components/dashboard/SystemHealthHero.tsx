import { BrainCircuit, Clock, ShieldCheck } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { systemHealth as defaultSystemHealth } from "@/data/placeholder";
import { cn } from "@/lib/utils";
import type { HealthStatus, SystemHealth } from "@/types/system";

const STATUS_CONFIG: Record<
  HealthStatus,
  { label: string; badgeVariant: "success" | "warning" | "danger"; ring: string }
> = {
  healthy: { label: "Healthy", badgeVariant: "success", ring: "stroke-success" },
  warning: { label: "Needs Attention", badgeVariant: "warning", ring: "stroke-warning" },
  critical: { label: "Critical", badgeVariant: "danger", ring: "stroke-danger" },
};

interface SystemHealthHeroProps {
  health?: SystemHealth;
}

// Primary hero card summarizing overall system health at a glance.
// Presentational — data flows in via props, defaulting to placeholder data.
export function SystemHealthHero({ health = defaultSystemHealth }: SystemHealthHeroProps) {
  const config = STATUS_CONFIG[health.status];
  const circumference = 2 * Math.PI * 42;
  const offset = circumference - (health.score / 100) * circumference;

  return (
    <Card className="p-6 shadow-soft">
      <div className="flex flex-col items-center gap-8 md:flex-row md:items-center">
        {/* Score ring — the page's hero figure, sized to dominate the card */}
        <div
          className="relative flex h-36 w-36 shrink-0 items-center justify-center"
          role="img"
          aria-label={`System health score: ${health.score} out of 100`}
        >
          <svg className="h-36 w-36 -rotate-90" viewBox="0 0 96 96" aria-hidden="true">
            <circle
              cx="48"
              cy="48"
              r="42"
              fill="none"
              strokeWidth="7"
              className="stroke-surface"
            />
            <circle
              cx="48"
              cy="48"
              r="42"
              fill="none"
              strokeWidth="7"
              strokeLinecap="round"
              strokeDasharray={circumference}
              strokeDashoffset={offset}
              className={cn("transition-all duration-700 ease-out", config.ring)}
            />
          </svg>
          <div className="absolute flex flex-col items-center" aria-hidden="true">
            <span className="text-4xl font-bold leading-none tracking-tight text-foreground">
              {health.score}
            </span>
            <span className="mt-1.5 text-2xs text-muted-foreground">/ 100</span>
          </div>
        </div>

        <Separator orientation="vertical" className="hidden h-24 md:block" />

        {/* Details */}
        <div className="flex flex-1 flex-col gap-4">
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="text-xl font-semibold tracking-tight text-foreground">System Health</h1>
            <Badge variant={config.badgeVariant}>{config.label}</Badge>
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div className="flex items-center gap-3 rounded-md border border-border bg-surface/60 px-4 py-3">
              <div className="flex h-8 w-8 items-center justify-center rounded-sm bg-primary/10 text-primary">
                <BrainCircuit aria-hidden="true" className="h-4 w-4" />
              </div>
              <div>
                <p className="text-2xs text-muted-foreground">AI Status</p>
                <p className="text-sm font-medium text-foreground">{health.aiStatus}</p>
              </div>
            </div>

            <div className="flex items-center gap-3 rounded-md border border-border bg-surface/60 px-4 py-3">
              <div className="flex h-8 w-8 items-center justify-center rounded-sm bg-success/10 text-success">
                <Clock aria-hidden="true" className="h-4 w-4" />
              </div>
              <div>
                <p className="text-2xs text-muted-foreground">Uptime</p>
                <p className="text-sm font-medium text-foreground">{health.uptime}</p>
              </div>
            </div>
          </div>
        </div>

        <div className="hidden shrink-0 flex-col items-end gap-1 self-start md:flex">
          <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
            <ShieldCheck aria-hidden="true" className="h-3.5 w-3.5 text-success" />
            Monitored continuously
          </div>
        </div>
      </div>
    </Card>
  );
}
