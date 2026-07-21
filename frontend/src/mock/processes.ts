// Mock data layer — "processes" domain. See server.ts for the function-vs-constant rationale.
import type { ProcessItem } from "@/types/system";

const processes: ProcessItem[] = [
  { pid: 1042, name: "node", user: "www-data", cpu: 24.3, memory: 512 },
  { pid: 883, name: "postgres", user: "postgres", cpu: 12.1, memory: 890 },
  { pid: 221, name: "nginx", user: "root", cpu: 4.6, memory: 64 },
  { pid: 1290, name: "docker-proxy", user: "root", cpu: 2.8, memory: 48 },
  { pid: 559, name: "systemd-journald", user: "root", cpu: 1.2, memory: 32 },
];

/** Mirrors GET /api/processes */
export function getProcesses(): ProcessItem[] {
  return processes;
}
