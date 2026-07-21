// Mock data layer — "quick actions" domain. See server.ts for the function-vs-constant
// rationale. Not one of the five named domains — added for full coverage (see insights.ts).
import type { QuickAction } from "@/types/system";

const quickActions: QuickAction[] = [
  { id: "qa-1", label: "Restart Service", description: "Restart a monitored service", icon: "restart" },
  { id: "qa-2", label: "Open Terminal", description: "SSH into this host", icon: "terminal" },
  { id: "qa-3", label: "Export Report", description: "Download a system health report", icon: "download" },
  { id: "qa-4", label: "Run Security Scan", description: "Trigger a manual vulnerability scan", icon: "shield" },
];

/** Mirrors GET /api/quick-actions */
export function getQuickActions(): QuickAction[] {
  return quickActions;
}
