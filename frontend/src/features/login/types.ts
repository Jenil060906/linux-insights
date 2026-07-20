// Types for the login/server-discovery feature.
//
// Deliberately NOT importing from `@/types/system` (the dashboard's domain
// types) even though the shapes overlap (both have a hostname/os/status
// notion). This feature is meant to be a self-contained module that gets
// wired to the dashboard later — keeping its types local means it can be
// swapped for a real discovery/auth API without touching dashboard code,
// and vice versa. The one deliberate seam between the two is in
// `src/app/App.tsx`, which maps a `SelectedServer` into the dashboard's
// `HostInfo` shape at the route boundary.

export type ServerHealth = "healthy" | "warning";

export interface DiscoveredServer {
  id: string;
  hostname: string;
  os: string;
  status: ServerHealth;
  /** Optional recency label, e.g. "Connected Recently". Omitted = never connected before. */
  lastSeenLabel?: string;
}

export type ConnectSource = "discovered" | "manual";

export interface SelectedServer {
  hostname: string;
  os: string;
  status: ServerHealth;
  ip?: string;
  port?: number;
  source: ConnectSource;
  connectedAt: string;
}
