import type { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

interface SectionHeaderProps {
  title: string;
  description?: string;
  icon?: LucideIcon;
  action?: React.ReactNode;
  className?: string;
}

// Consistent title row used above every dashboard section.
export function SectionHeader({
  title,
  description,
  icon: Icon,
  action,
  className,
}: SectionHeaderProps) {
  return (
    <div className={cn("flex items-center justify-between gap-4", className)}>
      <div className="flex items-center gap-2.5">
        {Icon && (
          <div className="flex h-7 w-7 items-center justify-center rounded-sm border border-border bg-surface text-muted-foreground">
            <Icon aria-hidden="true" className="h-4 w-4" />
          </div>
        )}
        <div>
          <h2 className="text-sm font-semibold text-foreground">{title}</h2>
          {description && (
            <p className="text-xs text-muted-foreground">{description}</p>
          )}
        </div>
      </div>
      {action}
    </div>
  );
}
