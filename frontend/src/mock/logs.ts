// Mock data layer — "logs" domain. See server.ts for the function-vs-constant rationale.
// Not one of the five named domains — added for full coverage (see insights.ts).
import type { LogEntry } from "@/types/system";

const logEntries: LogEntry[] = [
  { id: "log-1", timestamp: "14:32:08", level: "info", message: "Health check passed", service: "monitor-agent" },
  { id: "log-2", timestamp: "14:31:52", level: "warn", message: "Disk usage above 80% on /var", service: "disk-monitor" },
  { id: "log-3", timestamp: "14:30:11", level: "error", message: "Failed to connect to metrics collector", service: "collector" },
  { id: "log-4", timestamp: "14:29:47", level: "info", message: "Scheduled backup completed", service: "backup-service" },
  { id: "log-5", timestamp: "14:28:03", level: "debug", message: "Cache invalidated for key system:cpu", service: "cache" },
];

/** Mirrors GET /api/logs */
export function getLogEntries(): LogEntry[] {
  return logEntries;
}
