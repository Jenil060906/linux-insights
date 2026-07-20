import { cn } from "@/lib/utils";

// The generic "state" vocabulary — every place in the app that shows live
// state (connection, health, streaming) maps onto one of these four, never
// an arbitrary color. Mirrors the status color tokens in tailwind.config.ts.
export type StatusTone = "success" | "warning" | "danger" | "neutral";

const DOT_COLOR: Record<StatusTone, string> = {
  success: "bg-success",
  warning: "bg-warning",
  danger: "bg-danger",
  neutral: "bg-muted-foreground",
};

const TEXT_COLOR: Record<StatusTone, string> = {
  success: "text-success",
  warning: "text-warning",
  danger: "text-danger",
  neutral: "text-muted-foreground",
};

interface StatusIndicatorProps {
  tone: StatusTone;
  label: string;
  /** Animate the dot (a live/streaming feed). Off for a static, settled state. */
  pulse?: boolean;
  className?: string;
}

// Inline "dot + label" status readout — e.g. Header's connection status.
// Distinct from Badge: Badge is a pill for a value inside a card grid
// (severity, impact); StatusIndicator is bare text for a status line.
// Distinct from IconTile: IconTile marks *what something is*, this marks
// *what state it's in*.
export function StatusIndicator({ tone, label, pulse = true, className }: StatusIndicatorProps) {
  return (
    <span className={cn("inline-flex items-center gap-1.5 text-xs font-medium", TEXT_COLOR[tone], className)}>
      <span className="relative flex h-2 w-2 shrink-0" aria-hidden="true">
        {pulse && (
          <span
            className={cn(
              "absolute inline-flex h-full w-full motion-safe:animate-pulse-dot rounded-full",
              DOT_COLOR[tone]
            )}
          />
        )}
        <span className={cn("relative inline-flex h-2 w-2 rounded-full", DOT_COLOR[tone])} />
      </span>
      {label}
    </span>
  );
}
