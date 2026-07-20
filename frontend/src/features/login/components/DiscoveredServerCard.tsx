import { Server } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { IconTile } from "@/components/ui/icon-tile";
import type { DiscoveredServer } from "@/features/login/types";

const HEALTH_LABEL: Record<DiscoveredServer["status"], string> = {
  healthy: "Healthy",
  warning: "Needs Attention",
};

interface DiscoveredServerCardProps {
  server: DiscoveredServer;
  onConnect: (server: DiscoveredServer) => void;
}

// A single discovered-server row: identity + health on the left, a single
// Connect action on the right. Reuses IconTile/Badge/Button so this reads
// as the same design language as the dashboard, not a bolted-on screen.
export function DiscoveredServerCard({ server, onConnect }: DiscoveredServerCardProps) {
  return (
    <div className="flex items-center justify-between gap-3 rounded-md border border-border bg-surface/50 px-4 py-3 transition-colors hover:bg-surface/80">
      <div className="flex min-w-0 items-center gap-3">
        <IconTile icon={Server} tone="accent" size="md" />
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <p className="truncate text-sm font-semibold text-foreground">{server.hostname}</p>
            <Badge variant={server.status === "healthy" ? "success" : "warning"}>
              {HEALTH_LABEL[server.status]}
            </Badge>
          </div>
          <p className="text-2xs text-muted-foreground">
            {server.os}
            {server.lastSeenLabel ? ` · ${server.lastSeenLabel}` : ""}
          </p>
        </div>
      </div>
      <Button size="sm" onClick={() => onConnect(server)}>
        Connect
      </Button>
    </div>
  );
}
