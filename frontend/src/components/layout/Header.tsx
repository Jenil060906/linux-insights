import { Activity, Bell, LogOut, Server } from "lucide-react";
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
  /** Renders a Logout button when provided — omitted, the button doesn't appear. */
  onLogout?: () => void;
}

// Top-level app bar: identity, host status, and user actions.
export function Header({ host = defaultHostInfo, onLogout }: HeaderProps) {
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

        <Separator orientation="vertical" className="hidden h-6 lg:block" />

        {/* Host + connection status — progressively revealed so it never has
            to squeeze into a width it doesn't fit: hostname+status appear at
            lg (laptop), OS/last-sync/latency only once xl (desktop/large
            screens) confirms there's room — identical to today at >=1280px. */}
        <div className="hidden flex-1 items-center gap-4 lg:flex xl:gap-6">
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Server aria-hidden="true" className="h-3.5 w-3.5 shrink-0" />
            <span className="max-w-[140px] truncate font-medium text-foreground">
              {host.hostname}
            </span>
            <span className="hidden text-muted-foreground xl:inline">· {host.os}</span>
          </div>

          <StatusIndicator
            tone={CONNECTION_TONE[host.connectionStatus]}
            label={CONNECTION_LABEL[host.connectionStatus]}
          />

          <div className="hidden text-xs text-muted-foreground xl:block">
            Last sync <span className="text-foreground">{host.lastSyncedAt}</span>
          </div>

          <div className="hidden text-xs text-muted-foreground xl:block">
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

          {onLogout && (
            <Button variant="ghost" size="icon" aria-label="Log out" onClick={onLogout}>
              <LogOut aria-hidden="true" className="h-4 w-4" />
            </Button>
          )}
        </div>
      </div>
    </header>
  );
}
