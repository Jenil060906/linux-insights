// Static placeholder "discovery" results. No networking — a real discovery
// agent (mDNS/SSH probe/etc.) would populate this list in a later phase.
import type { DiscoveredServer } from "@/features/login/types";

export const discoveredServers: DiscoveredServer[] = [
  {
    id: "ubuntu-prod-01",
    hostname: "Ubuntu-Prod-01",
    os: "Ubuntu 22.04",
    status: "healthy",
    lastSeenLabel: "Connected Recently",
  },
  {
    id: "ubuntu-test",
    hostname: "Ubuntu-Test",
    os: "Ubuntu 24.04",
    status: "healthy",
  },
];
