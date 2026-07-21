// Mock data layer — "server" domain (the connected host + its overall health).
//
// Every export here is a FUNCTION, not a bare constant, deliberately mirroring
// what a REST client method will look like later:
//
//   export function getHostInfo(): HostInfo { return hostInfo; }
//   // becomes ->
//   export async function getHostInfo(): Promise<HostInfo> {
//     return fetch("/api/server").then((res) => res.json());
//   }
//
// Components already call these as functions (see Header/SystemHealthHero),
// so swapping sync -> async later is a one-line signature change per
// function plus wiring the call site to await/useEffect — the function
// names, shapes, and every consumer's data contract stay identical.
import type { HostInfo, SystemHealth } from "@/types/system";

const hostInfo: HostInfo = {
  hostname: "ubuntu-prod-01",
  os: "Ubuntu 22.04.4 LTS",
  connectionStatus: "connected",
  lastSyncedAt: "2 seconds ago",
  latencyMs: 18,
};

const systemHealth: SystemHealth = {
  score: 94,
  status: "healthy",
  aiStatus: "No anomalies detected",
  uptime: "14d 6h 32m",
};

/** Mirrors GET /api/server */
export function getHostInfo(): HostInfo {
  return hostInfo;
}

/** Mirrors GET /api/server/health */
export function getSystemHealth(): SystemHealth {
  return systemHealth;
}
