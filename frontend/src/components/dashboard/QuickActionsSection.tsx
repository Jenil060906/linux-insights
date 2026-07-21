import { memo } from "react";
import { Download, RefreshCw, Settings, Shield, Terminal, Zap, type LucideIcon } from "lucide-react";
import { SectionCard } from "@/components/common/SectionCard";
import { Badge } from "@/components/ui/badge";
import { IconTile } from "@/components/ui/icon-tile";
import { getQuickActions } from "@/mock/quickActions";
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

// Grid of common operator actions. Presentational, non-functional in Phase 1
// (no backend wiring). Memoized: gets no props from DashboardPage, so it's
// excluded from the once-a-second re-render the live metric tick otherwise
// triggers.
export const QuickActionsSection = memo(function QuickActionsSection({
  actions = getQuickActions(),
}: QuickActionsSectionProps) {
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
              <IconTile icon={Icon} tone="accent" size="lg" />
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
});
