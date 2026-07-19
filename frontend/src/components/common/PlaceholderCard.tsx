import type { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

interface PlaceholderCardProps {
  icon?: LucideIcon;
  label: string;
  className?: string;
}

// Generic "coming soon" filler used by sections that don't have live data/charts yet.
export function PlaceholderCard({ icon: Icon, label, className }: PlaceholderCardProps) {
  return (
    <div
      className={cn(
        "flex min-h-[160px] flex-col items-center justify-center gap-2 rounded-md border border-dashed border-border bg-surface/40 text-center",
        className
      )}
    >
      {Icon && <Icon aria-hidden="true" className="h-5 w-5 text-muted-foreground" />}
      <p className="text-xs text-muted-foreground">{label}</p>
    </div>
  );
}
