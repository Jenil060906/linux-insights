import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  type TooltipProps,
} from "recharts";
import { chartTheme } from "@/charts/theme";
import type { TimeSeriesPoint } from "@/types/system";

interface UsageAreaChartProps {
  data: TimeSeriesPoint[];
  unit?: string;
  color?: string;
  height?: number;
}

function ChartTooltip({ active, payload, label, unit }: TooltipProps<number, string> & { unit: string }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-md border border-border bg-surface px-3 py-2 text-xs shadow-soft">
      <p className="text-muted-foreground">{label}</p>
      <p className="mt-0.5 font-semibold text-foreground">
        {payload[0].value}
        {unit}
      </p>
    </div>
  );
}

// Single-series usage-over-time chart: one hue, flat (non-gradient) area wash,
// hairline grid, hover tooltip. Shared by every Live Monitoring tab.
export function UsageAreaChart({ data, unit = "%", color = chartTheme.primary, height = 220 }: UsageAreaChartProps) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={data} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
        <CartesianGrid vertical={false} stroke={chartTheme.border} />
        <XAxis
          dataKey="time"
          tickLine={false}
          axisLine={false}
          tick={{ fill: chartTheme.mutedForeground, fontSize: 11 }}
          minTickGap={24}
        />
        <YAxis
          tickLine={false}
          axisLine={false}
          tick={{ fill: chartTheme.mutedForeground, fontSize: 11 }}
          width={40}
          tickFormatter={(value: number) => `${value}${unit}`}
        />
        <Tooltip cursor={{ stroke: chartTheme.border, strokeWidth: 1 }} content={<ChartTooltip unit={unit} />} />
        <Area
          type="monotone"
          dataKey="value"
          stroke={color}
          strokeWidth={2}
          fill={color}
          fillOpacity={0.1}
          dot={false}
          activeDot={{ r: 5, stroke: chartTheme.border, strokeWidth: 2 }}
          isAnimationActive
          animationDuration={600}
          animationEasing="ease-out"
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
