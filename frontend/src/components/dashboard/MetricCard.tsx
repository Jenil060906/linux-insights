import { motion } from "framer-motion";
import { TrendingDown, TrendingUp, Minus } from "lucide-react";
import { Card } from "@/components/ui/card";
import { IconTile } from "@/components/ui/icon-tile";
import { MiniSparkline } from "@/components/common/MiniSparkline";
import { useAnimatedSeries } from "@/hooks/useAnimatedSeries";
import { cn } from "@/lib/utils";
import type { MetricCardData } from "@/types/system";

const TREND_CONFIG = {
  up: { icon: TrendingUp, className: "text-danger" },
  down: { icon: TrendingDown, className: "text-success" },
  flat: { icon: Minus, className: "text-muted-foreground" },
} as const;

// Single metric tile: icon, current value, trend delta, and a sparkline.
// `data.icon` is a LucideIcon component supplied by the caller (not a closed
// enum resolved internally) — this is what makes MetricCard a genuine design
// system atom rather than a component hardcoded to four specific metrics.
export function MetricCard({ data }: { data: MetricCardData }) {
  const trend = TREND_CONFIG[data.trend];
  const TrendIcon = trend.icon;
  // Sparkline values arrive as a fresh array every tick (live or static) —
  // tween toward each new shape instead of snapping to it.
  const animatedSparkline = useAnimatedSeries(data.sparkline);

  return (
    <Card className="p-4 transition-shadow duration-200 hover:shadow-soft">
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-2.5">
          <IconTile icon={data.icon} tone="accent" size="md" />
          <p className="text-xs font-medium text-muted-foreground">{data.label}</p>
        </div>
        <div className={cn("flex items-center gap-1 text-xs font-medium", trend.className)}>
          <TrendIcon aria-hidden="true" className="h-3.5 w-3.5" />
          {data.trendValue}
        </div>
      </div>

      <div className="mt-3 flex items-baseline gap-1.5">
        {/* Remounting on value change replays the fade-in — a lightweight
            "this just updated" cue for the live ticker. */}
        <motion.span
          key={data.value}
          initial={{ opacity: 0.35 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.35, ease: "easeOut" }}
          className="text-2xl font-bold tabular-nums text-foreground"
        >
          {data.value}
        </motion.span>
        {data.unit && <span className="text-xs text-muted-foreground">{data.unit}</span>}
      </div>

      <div className="mt-3" aria-hidden="true">
        <MiniSparkline data={animatedSparkline} />
      </div>
    </Card>
  );
}
