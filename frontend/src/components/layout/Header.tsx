import { Activity, Bell, Server } from "lucide-react";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { StatusIndicator, type StatusTone } from "@/components/ui/status-indicator";
import { Clock } from "@/components/layout/Clock";
import { hostInfo as defaultHostInfo } from "@/data/placeholder";
import type { HostInfo, ConnectionStatus } from "@/types/system";

const CONNECTION_LABEL: Record<ConnectionStatus, string> = {
  connected: "Connected",
  degraded: "Degraded",
  disconnected: "Disconnected",
};

const CONNECTION_TONE: Record<ConnectionStatus, StatusTone> = {
  connected: "success",
  degraded: "warning",
  disconnected: "danger",
};

interface HeaderProps {
  host?: HostInfo;
}

// Top-level app bar: identity, host status, and user actions.
export function Header({ host = defaultHostInfo }: HeaderProps) {
  return (
    <header className="sticky top-0 z-40 border-b border-border bg-surface/95 backdrop-blur supports-[backdrop-filter]:bg-surface/80">
      <div className="flex h-14 items-center justify-between gap-4 px-6">
        {/* Logo + product identity */}
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-md bg-primary">
            <Activity aria-hidden="true" className="h-4 w-4 text-primary-foreground" strokeWidth={2.5} />
          </div>
          <div className="hidden sm:block">
            <p className="text-sm font-semibold leading-none text-foreground">
              Linux Insight
            </p>
            <p className="text-2xs leading-none text-muted-foreground mt-0.5">
              System Monitoring
            </p>
          </div>
        </div>

        <Separator orientation="vertical" className="hidden h-6 md:block" />

        {/* Host + connection status */}
        <div className="hidden flex-1 items-center gap-6 md:flex">
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Server aria-hidden="true" className="h-3.5 w-3.5" />
            <span className="font-medium text-foreground">{host.hostname}</span>
            <span className="text-muted-foreground">· {host.os}</span>
          </div>

          <StatusIndicator
            tone={CONNECTION_TONE[host.connectionStatus]}
            label={CONNECTION_LABEL[host.connectionStatus]}
          />

          <div className="text-xs text-muted-foreground">
            Last sync <span className="text-foreground">{host.lastSyncedAt}</span>
          </div>

          <div className="text-xs text-muted-foreground">
            Latency <span className="text-foreground">{host.latencyMs}ms</span>
          </div>
        </div>

        {/* Clock + actions */}
        <div className="flex items-center gap-3">
          <Clock />

          <Separator orientation="vertical" className="hidden h-6 lg:block" />

          <Button variant="ghost" size="icon" className="relative" aria-label="Notifications">
            <Bell aria-hidden="true" className="h-4 w-4" />
            <span className="absolute right-1.5 top-1.5 h-1.5 w-1.5 rounded-full bg-danger" aria-hidden="true" />
          </Button>

          <Avatar className="h-8 w-8">
            <AvatarFallback aria-label="User: JV">JV</AvatarFallback>
          </Avatar>
        </div>
      </div>
    </header>
  );
}
