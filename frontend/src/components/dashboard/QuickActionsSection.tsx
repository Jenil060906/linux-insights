import { Download, RefreshCw, Settings, Shield, Terminal, Zap, type LucideIcon } from "lucide-react";
import { SectionCard } from "@/components/common/SectionCard";
import { Badge } from "@/components/ui/badge";
import { quickActions as defaultQuickActions } from "@/data/placeholder";
import type { QuickAction } from "@/types/system";

const ICON_MAP: Record<QuickAction["icon"], LucideIcon> = {
  restart: RefreshCw,
  terminal: Terminal,
  download: Download,
  shield: Shield,
  refresh: RefreshCw,
  settings: Settings,
};

interface QuickActionsSectionProps {
  actions?: QuickAction[];
}

// Grid of common operator actions. Presentational, non-functional in Phase 1 (no backend wiring).
export function QuickActionsSection({ actions = defaultQuickActions }: QuickActionsSectionProps) {
  return (
    <SectionCard title="Quick Actions" description="Common operator tasks" icon={Zap}>
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        {actions.map((action) => {
          const Icon = ICON_MAP[action.icon];
          return (
            <button
              key={action.id}
              type="button"
              disabled
              aria-label={`${action.label} (coming soon)`}
              title="Coming soon"
              className="group relative flex items-center gap-3 rounded-md border border-border bg-surface/50 px-3 py-3 text-left transition-colors hover:bg-surface focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40 disabled:cursor-not-allowed disabled:opacity-70"
            >
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-sm border border-border bg-surface text-primary">
                <Icon aria-hidden="true" className="h-4 w-4" />
              </div>
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium text-foreground">{action.label}</p>
                <p className="truncate text-2xs text-muted-foreground">{action.description}</p>
              </div>
              <Badge variant="outline" className="shrink-0">
                Soon
              </Badge>
            </button>
          );
        })}
      </div>
    </SectionCard>
  );
}
