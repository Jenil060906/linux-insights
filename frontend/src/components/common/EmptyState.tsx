import type { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

interface EmptyStateProps {
  icon?: LucideIcon;
  message: string;
  /** Set false when already inside a bordered container (e.g. a ScrollArea) to avoid a double frame. */
  bordered?: boolean;
  className?: string;
}

// Shared "nothing to show for this filter" treatment — icon + message,
// optionally boxed in a dashed border. Used wherever a list can filter down
// to zero rows (Alerts, Logs) so every empty state in the app reads as the
// same deliberate pattern rather than an ad hoc leftover string.
//
// Distinct from PlaceholderCard: that one marks a feature with no real
// content *yet* (a build-time stand-in); this one is a genuine runtime UI
// state a filtered list can always reach, backend or not.
export function EmptyState({ icon: Icon, message, bordered = true, className }: EmptyStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center gap-2 px-3 py-8 text-center",
        bordered && "rounded-md border border-dashed border-border bg-surface/40",
        className
      )}
    >
      {Icon && <Icon aria-hidden="true" className="h-5 w-5 text-muted-foreground" />}
      <p className="text-xs text-muted-foreground">{message}</p>
    </div>
  );
}
