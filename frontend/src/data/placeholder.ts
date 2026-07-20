// Static placeholder data for the Phase 1 dashboard shell.
// No API calls, no live values — swapped for real telemetry in a later phase.

import { Cpu, HardDrive, MemoryStick, Wifi } from "lucide-react";
import type {
  AIInsight,
  AlertItem,
  HostInfo,
  LogEntry,
  MetricCardData,
  MetricKey,
  ProcessItem,
  QuickAction,
  SystemHealth,
  TimeSeriesPoint,
} from "@/types/system";

export const hostInfo: HostInfo = {
  hostname: "ubuntu-prod-01",
  os: "Ubuntu 22.04.4 LTS",
  connectionStatus: "connected",
  lastSyncedAt: "2 seconds ago",
  latencyMs: 18,
};

export const systemHealth: SystemHealth = {
  score: 94,
  status: "healthy",
  aiStatus: "No anomalies detected",
  uptime: "14d 6h 32m",
};

export const metricCards: MetricCardData[] = [
  {
    id: "cpu",
    label: "CPU Usage",
    value: "42",
    unit: "%",
    trend: "up",
    trendValue: "+3.2%",
    sparkline: [30, 34, 32, 38, 36, 40, 42],
    icon: Cpu,
  },
  {
    id: "ram",
    label: "Memory Usage",
    value: "6.8",
    unit: "GB / 16GB",
    trend: "flat",
    trendValue: "+0.1%",
    sparkline: [40, 42, 41, 43, 42, 42, 43],
    icon: MemoryStick,
  },
  {
    id: "disk",
    label: "Disk Usage",
    value: "218",
    unit: "GB / 512GB",
    trend: "up",
    trendValue: "+0.8%",
    sparkline: [38, 39, 39, 40, 41, 41, 42],
    icon: HardDrive,
  },
  {
    id: "network",
    label: "Network I/O",
    value: "1.4",
    unit: "MB/s",
    trend: "down",
    trendValue: "-5.4%",
    sparkline: [22, 26, 24, 20, 18, 16, 15],
    icon: Wifi,
  },
];

export const alerts: AlertItem[] = [
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

export const topProcesses: ProcessItem[] = [
  { pid: 1042, name: "node", user: "www-data", cpu: 24.3, memory: 512 },
  { pid: 883, name: "postgres", user: "postgres", cpu: 12.1, memory: 890 },
  { pid: 221, name: "nginx", user: "root", cpu: 4.6, memory: 64 },
  { pid: 1290, name: "docker-proxy", user: "root", cpu: 2.8, memory: 48 },
  { pid: 559, name: "systemd-journald", user: "root", cpu: 1.2, memory: 32 },
];

export const logEntries: LogEntry[] = [
  { id: "log-1", timestamp: "14:32:08", level: "info", message: "Health check passed", service: "monitor-agent" },
  { id: "log-2", timestamp: "14:31:52", level: "warn", message: "Disk usage above 80% on /var", service: "disk-monitor" },
  { id: "log-3", timestamp: "14:30:11", level: "error", message: "Failed to connect to metrics collector", service: "collector" },
  { id: "log-4", timestamp: "14:29:47", level: "info", message: "Scheduled backup completed", service: "backup-service" },
  { id: "log-5", timestamp: "14:28:03", level: "debug", message: "Cache invalidated for key system:cpu", service: "cache" },
];

export const quickActions: QuickAction[] = [
  { id: "qa-1", label: "Restart Service", description: "Restart a monitored service", icon: "restart" },
  { id: "qa-2", label: "Open Terminal", description: "SSH into this host", icon: "terminal" },
  { id: "qa-3", label: "Export Report", description: "Download a system health report", icon: "download" },
  { id: "qa-4", label: "Run Security Scan", description: "Trigger a manual vulnerability scan", icon: "shield" },
];

// 60 minutes of 5-minute-interval samples per metric — static, for the Live Monitoring chart.
export const liveMonitoringSeries: Record<MetricKey, TimeSeriesPoint[]> = {
  cpu: [
    { time: "13:35", value: 31 },
    { time: "13:40", value: 34 },
    { time: "13:45", value: 29 },
    { time: "13:50", value: 38 },
    { time: "13:55", value: 44 },
    { time: "14:00", value: 40 },
    { time: "14:05", value: 36 },
    { time: "14:10", value: 41 },
    { time: "14:15", value: 47 },
    { time: "14:20", value: 39 },
    { time: "14:25", value: 43 },
    { time: "14:30", value: 42 },
  ],
  ram: [
    { time: "13:35", value: 39 },
    { time: "13:40", value: 40 },
    { time: "13:45", value: 40 },
    { time: "13:50", value: 41 },
    { time: "13:55", value: 42 },
    { time: "14:00", value: 41 },
    { time: "14:05", value: 42 },
    { time: "14:10", value: 43 },
    { time: "14:15", value: 43 },
    { time: "14:20", value: 42 },
    { time: "14:25", value: 43 },
    { time: "14:30", value: 43 },
  ],
  disk: [
    { time: "13:35", value: 40 },
    { time: "13:40", value: 40 },
    { time: "13:45", value: 40 },
    { time: "13:50", value: 41 },
    { time: "13:55", value: 41 },
    { time: "14:00", value: 41 },
    { time: "14:05", value: 41 },
    { time: "14:10", value: 42 },
    { time: "14:15", value: 42 },
    { time: "14:20", value: 42 },
    { time: "14:25", value: 42 },
    { time: "14:30", value: 43 },
  ],
  network: [
    { time: "13:35", value: 0.9 },
    { time: "13:40", value: 1.3 },
    { time: "13:45", value: 1.1 },
    { time: "13:50", value: 1.8 },
    { time: "13:55", value: 2.1 },
    { time: "14:00", value: 1.6 },
    { time: "14:05", value: 1.2 },
    { time: "14:10", value: 1.5 },
    { time: "14:15", value: 1.9 },
    { time: "14:20", value: 1.3 },
    { time: "14:25", value: 1.1 },
    { time: "14:30", value: 1.4 },
  ],
};

export const aiInsights: AIInsight[] = [
  {
    id: "insight-1",
    category: "performance",
    impact: "medium",
    title: "Memory usage trending upward over 7 days",
    description:
      "Node process memory has grown ~8% week-over-week. Likely candidate: a slow leak in the request cache layer.",
    timestamp: "10 min ago",
  },
  {
    id: "insight-2",
    category: "security",
    impact: "high",
    title: "Unusual SSH access pattern detected",
    description:
      "Login attempts from a new geographic region were correlated with the auth-monitor alert. Recommend reviewing recent sessions.",
    timestamp: "1 hour ago",
  },
  {
    id: "insight-3",
    category: "cost",
    impact: "low",
    title: "Disk headroom sufficient for 40+ days",
    description:
      "At current growth rate, /var will not reach capacity for at least 40 days — no immediate action needed.",
    timestamp: "3 hours ago",
  },
];
