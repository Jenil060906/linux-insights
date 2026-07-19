import type { ButtonHTMLAttributes } from "react";
import type { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

interface ChipProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  active?: boolean;
  icon?: LucideIcon;
  count?: number;
}

// Shared pill-button used by every filter/tab row (Live Monitoring metrics,
// Alerts severity, Logs level) so hover/active/spacing stay pixel-identical.
export function Chip({ active, icon: Icon, count, className, children, ...props }: ChipProps) {
  return (
    <button
      type="button"
      aria-pressed={active}
      className={cn(
        "flex items-center gap-1.5 rounded-sm border px-2.5 py-1.5 text-xs font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40",
        active
          ? "border-primary/30 bg-primary/10 text-primary"
          : "border-border bg-surface text-muted-foreground hover:border-border hover:bg-card hover:text-foreground",
        className
      )}
      {...props}
    >
      {Icon && <Icon aria-hidden="true" className="h-3.5 w-3.5" />}
      {children}
      {typeof count === "number" && (
        <span className="text-2xs tabular-nums text-muted-foreground">{count}</span>
      )}
    </button>
  );
}
