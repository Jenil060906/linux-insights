import { memo } from "react";
import { AlertTriangle, Bug, Info, ListFilter, OctagonAlert, ScrollText, type LucideIcon } from "lucide-react";
import { SectionCard } from "@/components/common/SectionCard";
import { FilterChipRow, type FilterOption } from "@/components/common/FilterChipRow";
import { EmptyState } from "@/components/common/EmptyState";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useCategoryFilter, type CategoryFilter } from "@/hooks/useCategoryFilter";
import { cn } from "@/lib/utils";
import { getLogEntries } from "@/mock/logs";
import type { LogEntry } from "@/types/system";

type LogLevel = LogEntry["level"];

const LEVEL_CONFIG: Record<LogLevel, { icon: LucideIcon; textClassName: string; borderClassName: string }> = {
  info: { icon: Info, textClassName: "text-primary", borderClassName: "border-l-primary" },
  warn: { icon: AlertTriangle, textClassName: "text-warning", borderClassName: "border-l-warning" },
  error: { icon: OctagonAlert, textClassName: "text-danger", borderClassName: "border-l-danger" },
  debug: { icon: Bug, textClassName: "text-muted-foreground", borderClassName: "border-l-border" },
};

const LOG_LEVELS: LogLevel[] = ["info", "warn", "error", "debug"];
const getLogLevel = (log: LogEntry) => log.level;

const FILTER_OPTIONS: FilterOption<CategoryFilter<LogLevel>>[] = [
  { key: "all", label: "All", icon: ListFilter },
  { key: "info", label: "Info", icon: LEVEL_CONFIG.info.icon },
  { key: "warn", label: "Warn", icon: LEVEL_CONFIG.warn.icon },
  { key: "error", label: "Error", icon: LEVEL_CONFIG.error.icon },
  { key: "debug", label: "Debug", icon: LEVEL_CONFIG.debug.icon },
];

interface LogsSectionProps {
  logs?: LogEntry[];
}

// Tailing system log feed with client-side level filtering. Presentational —
// data flows in via props. Memoized for the same reason as AlertsSection:
// no props from DashboardPage means it never needs to re-render on the
// once-a-second live metric tick.
export const LogsSection = memo(function LogsSection({ logs = getLogEntries() }: LogsSectionProps) {
  const {
    filter,
    setFilter,
    counts,
    visibleItems: visibleLogs,
  } = useCategoryFilter(logs, getLogLevel, LOG_LEVELS);

  return (
    <SectionCard title="Logs" description="Latest system events" icon={ScrollText}>
      <FilterChipRow
        groupLabel="Filter logs by level"
        options={FILTER_OPTIONS}
        active={filter}
        counts={counts}
        onChange={setFilter}
      />

      <ScrollArea className="h-[220px] rounded-md border border-border bg-surface/50">
        {visibleLogs.length === 0 ? (
          <EmptyState
            icon={ScrollText}
            message="No log entries at this level."
            bordered={false}
            className="h-full py-0"
          />
        ) : (
          <div className="flex flex-col divide-y divide-border font-mono text-xs">
            {visibleLogs.map((log) => {
              const config = LEVEL_CONFIG[log.level];
              return (
                <div
                  key={log.id}
                  className={cn(
                    "flex items-start gap-3 border-l-2 px-3 py-2 transition-colors hover:bg-surface",
                    config.borderClassName
                  )}
                >
                  <span className="shrink-0 text-muted-foreground">{log.timestamp}</span>
                  <span className={cn("shrink-0 w-12 uppercase", config.textClassName)}>{log.level}</span>
                  <span className="shrink-0 text-muted-foreground">[{log.service}]</span>
                  <span className="text-foreground">{log.message}</span>
                </div>
              );
            })}
          </div>
        )}
      </ScrollArea>
    </SectionCard>
  );
});
