// Shared domain types for the Linux Insight dashboard shell.
// Phase 1 only — these describe placeholder data shapes, not live telemetry.

import type { LucideIcon } from "lucide-react";

export type ConnectionStatus = "connected" | "degraded" | "disconnected";

export type TrendDirection = "up" | "down" | "flat";

export type HealthStatus = "healthy" | "warning" | "critical";

export type AlertSeverity = "critical" | "warning" | "info";

export type MetricKey = "cpu" | "ram" | "disk" | "network";

export type InsightCategory = "performance" | "security" | "cost" | "reliability";

export type InsightImpact = "low" | "medium" | "high";

export interface HostInfo {
  hostname: string;
  os: string;
  connectionStatus: ConnectionStatus;
  lastSyncedAt: string;
  latencyMs: number;
}

export interface MetricCardData {
  id: string;
  label: string;
  value: string;
  unit?: string;
  trend: TrendDirection;
  trendValue: string;
  sparkline: number[];
  icon: LucideIcon;
}

export interface TimeSeriesPoint {
  time: string;
  value: number;
}

export interface AIInsight {
  id: string;
  category: InsightCategory;
  impact: InsightImpact;
  title: string;
  description: string;
  timestamp: string;
}

export interface SystemHealth {
  score: number;
  status: HealthStatus;
  aiStatus: string;
  uptime: string;
}

export interface AlertItem {
  id: string;
  severity: AlertSeverity;
  title: string;
  source: string;
  timestamp: string;
}

export interface ProcessItem {
  pid: number;
  name: string;
  user: string;
  cpu: number;
  memory: number;
}

export interface LogEntry {
  id: string;
  timestamp: string;
  level: "info" | "warn" | "error" | "debug";
  message: string;
  service: string;
}

export interface QuickAction {
  id: string;
  label: string;
  description: string;
  icon: "restart" | "terminal" | "download" | "shield" | "refresh" | "settings";
}

export interface AnalyticsPanel {
  id: string;
  label: string;
}
