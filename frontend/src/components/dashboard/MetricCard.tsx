import { Cpu, HardDrive, MemoryStick, TrendingDown, TrendingUp, Wifi, Minus } from "lucide-react";
import { Card } from "@/components/ui/card";
import { MiniSparkline } from "@/components/common/MiniSparkline";
import { cn } from "@/lib/utils";
import type { MetricCardData } from "@/types/system";

const ICON_MAP = {
  cpu: Cpu,
  ram: MemoryStick,
  disk: HardDrive,
  network: Wifi,
} as const;

const TREND_CONFIG = {
  up: { icon: TrendingUp, className: "text-danger" },
  down: { icon: TrendingDown, className: "text-success" },
  flat: { icon: Minus, className: "text-muted-foreground" },
} as const;

// Single metric tile: icon, current value, trend delta, and a sparkline.
export function MetricCard({ data }: { data: MetricCardData }) {
  const Icon = ICON_MAP[data.icon];
  const trend = TREND_CONFIG[data.trend];
  const TrendIcon = trend.icon;

  return (
    <Card className="p-4">
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-sm border border-border bg-surface text-primary">
            <Icon aria-hidden="true" className="h-4 w-4" />
          </div>
          <p className="text-xs font-medium text-muted-foreground">{data.label}</p>
        </div>
        <div className={cn("flex items-center gap-1 text-xs font-medium", trend.className)}>
          <TrendIcon aria-hidden="true" className="h-3.5 w-3.5" />
          {data.trendValue}
        </div>
      </div>

      <div className="mt-3 flex items-baseline gap-1.5">
        <span className="text-2xl font-bold tabular-nums text-foreground">{data.value}</span>
        {data.unit && <span className="text-xs text-muted-foreground">{data.unit}</span>}
      </div>

      <div className="mt-3" aria-hidden="true">
        <MiniSparkline data={data.sparkline} />
      </div>
    </Card>
  );
}
