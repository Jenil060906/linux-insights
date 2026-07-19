import { cn } from "@/lib/utils";

interface UsageBarProps {
  value: number;
  max?: number;
  className?: string;
  barClassName?: string;
}

// Small inline meter: filled track (accent) over an unfilled track (surface step).
export function UsageBar({ value, max = 100, className, barClassName }: UsageBarProps) {
  const percent = Math.min(100, Math.max(0, (value / max) * 100));
  return (
    <div
      role="progressbar"
      aria-valuenow={Math.round(percent)}
      aria-valuemin={0}
      aria-valuemax={100}
      className={cn("h-1.5 w-full overflow-hidden rounded-full bg-surface", className)}
    >
      <div
        className={cn("h-full rounded-full bg-primary", barClassName)}
        style={{ width: `${percent}%` }}
      />
    </div>
  );
}
