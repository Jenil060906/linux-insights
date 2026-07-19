import { cn } from "@/lib/utils";
import type { ConnectionStatus } from "@/types/system";

const STATUS_COLOR: Record<ConnectionStatus, string> = {
  connected: "bg-success",
  degraded: "bg-warning",
  disconnected: "bg-danger",
};

export function StatusDot({ status }: { status: ConnectionStatus }) {
  return (
    <span className="relative flex h-2 w-2" aria-hidden="true">
      <span
        className={cn(
          "absolute inline-flex h-full w-full motion-safe:animate-pulse-dot rounded-full",
          STATUS_COLOR[status]
        )}
      />
      <span className={cn("relative inline-flex h-2 w-2 rounded-full", STATUS_COLOR[status])} />
    </span>
  );
}
