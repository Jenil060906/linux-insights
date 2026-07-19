import { useMemo, useState } from "react";
import { AlertTriangle, Bug, Info, ListFilter, OctagonAlert, ScrollText, type LucideIcon } from "lucide-react";
import { SectionCard } from "@/components/common/SectionCard";
import { Chip } from "@/components/common/Chip";
import { ScrollArea } from "@/components/ui/scroll-area";
import { cn } from "@/lib/utils";
import { logEntries as defaultLogEntries } from "@/data/placeholder";
import type { LogEntry } from "@/types/system";

const LEVEL_COLOR: Record<LogEntry["level"], string> = {
  info: "text-primary",
  warn: "text-warning",
  error: "text-danger",
  debug: "text-muted-foreground",
};

const LEVEL_BORDER: Record<LogEntry["level"], string> = {
  info: "border-l-primary",
  warn: "border-l-warning",
  error: "border-l-danger",
  debug: "border-l-border",
};

const LEVEL_ICON: Record<LogEntry["level"], LucideIcon> = {
  info: Info,
  warn: AlertTriangle,
  error: OctagonAlert,
  debug: Bug,
};

type LevelFilter = "all" | LogEntry["level"];

interface LogsSectionProps {
  logs?: LogEntry[];
}

// Tailing system log feed with client-side level filtering. Presentational — data flows in via props.
export function LogsSection({ logs = defaultLogEntries }: LogsSectionProps) {
  const [filter, setFilter] = useState<LevelFilter>("all");

  const counts = useMemo(() => {
    return logs.reduce<Record<LevelFilter, number>>(
      (acc, log) => {
        acc.all += 1;
        acc[log.level] += 1;
        return acc;
      },
      { all: 0, info: 0, warn: 0, error: 0, debug: 0 }
    );
  }, [logs]);

  const visibleLogs = filter === "all" ? logs : logs.filter((log) => log.level === filter);

  const filters: { key: LevelFilter; label: string; icon?: LucideIcon }[] = [
    { key: "all", label: "All", icon: ListFilter },
    { key: "info", label: "Info", icon: LEVEL_ICON.info },
    { key: "warn", label: "Warn", icon: LEVEL_ICON.warn },
    { key: "error", label: "Error", icon: LEVEL_ICON.error },
    { key: "debug", label: "Debug", icon: LEVEL_ICON.debug },
  ];

  return (
    <SectionCard title="Logs" description="Latest system events" icon={ScrollText}>
      <div role="group" aria-label="Filter logs by level" className="mb-4 flex flex-wrap gap-1.5">
        {filters.map((item) => (
          <Chip
            key={item.key}
            icon={item.icon}
            active={filter === item.key}
            count={counts[item.key]}
            onClick={() => setFilter(item.key)}
          >
            {item.label}
          </Chip>
        ))}
      </div>

      <ScrollArea className="h-[220px] rounded-md border border-border bg-surface/50">
        {visibleLogs.length === 0 ? (
          <p className="px-3 py-6 text-center text-xs text-muted-foreground">
            No log entries at this level.
          </p>
        ) : (
          <div className="flex flex-col divide-y divide-border font-mono text-xs">
            {visibleLogs.map((log) => (
              <div
                key={log.id}
                className={cn(
                  "flex items-start gap-3 border-l-2 px-3 py-2 transition-colors hover:bg-surface",
                  LEVEL_BORDER[log.level]
                )}
              >
                <span className="shrink-0 text-muted-foreground">{log.timestamp}</span>
                <span className={cn("shrink-0 w-12 uppercase", LEVEL_COLOR[log.level])}>
                  {log.level}
                </span>
                <span className="shrink-0 text-muted-foreground">[{log.service}]</span>
                <span className="text-foreground">{log.message}</span>
              </div>
            ))}
          </div>
        )}
      </ScrollArea>
    </SectionCard>
  );
}
