// Mock data layer — "alerts" domain. See server.ts for the function-vs-constant rationale.
import type { AlertItem } from "@/types/system";

const alerts: AlertItem[] = [
  {
    id: "alert-1",
    severity: "warning",
    title: "Disk usage on /var approaching threshold",
    source: "disk-monitor",
    timestamp: "5 min ago",
  },
  {
    id: "alert-2",
    severity: "info",
    title: "Kernel update available (6.8.0-45)",
    source: "package-manager",
    timestamp: "22 min ago",
  },
  {
    id: "alert-3",
    severity: "critical",
    title: "SSH login from unrecognized IP",
    source: "auth-monitor",
    timestamp: "1 hour ago",
  },
];

/** Mirrors GET /api/alerts */
export function getAlerts(): AlertItem[] {
  return alerts;
}
