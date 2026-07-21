import { ListTree } from "lucide-react";
import { SectionCard } from "@/components/common/SectionCard";
import { UsageBar } from "@/components/common/UsageBar";
import { cn } from "@/lib/utils";
import { getProcesses } from "@/mock/processes";
import type { ProcessItem } from "@/types/system";

interface TopProcessesSectionProps {
  processes?: ProcessItem[];
}

// Top processes by CPU usage, with inline usage meters scaled to the list's own max.
// Presentational — data flows in via props.
export function TopProcessesSection({ processes = getProcesses() }: TopProcessesSectionProps) {
  const maxCpu = Math.max(...processes.map((p) => p.cpu), 1);
  const maxMemory = Math.max(...processes.map((p) => p.memory), 1);

  return (
    <SectionCard title="Top Processes" description="Ranked by CPU usage" icon={ListTree}>
      <div className="overflow-x-auto rounded-md border border-border">
        <table className="w-full min-w-[520px] text-left text-sm">
          <caption className="sr-only">Top processes ranked by CPU usage</caption>
          <thead>
            <tr className="border-b border-border bg-surface/60 text-2xs uppercase tracking-wide text-muted-foreground">
              <th scope="col" className="px-3 py-2 font-medium">PID</th>
              <th scope="col" className="px-3 py-2 font-medium">Process</th>
              <th scope="col" className="px-3 py-2 font-medium">User</th>
              <th scope="col" className="px-3 py-2 font-medium">CPU</th>
              <th scope="col" className="px-3 py-2 font-medium">Memory</th>
            </tr>
          </thead>
          <tbody>
            {processes.map((proc, i) => (
              <tr
                key={proc.pid}
                className={cn(
                  "transition-colors hover:bg-surface/40",
                  i !== processes.length - 1 && "border-b border-border"
                )}
              >
                <td className="px-3 py-2 font-mono text-xs text-muted-foreground">{proc.pid}</td>
                <td className="px-3 py-2 font-medium text-foreground">{proc.name}</td>
                <td className="px-3 py-2 text-muted-foreground">{proc.user}</td>
                <td className="px-3 py-2">
                  <div className="flex items-center gap-2">
                    <span className="w-10 shrink-0 text-right tabular-nums text-foreground">
                      {proc.cpu.toFixed(1)}%
                    </span>
                    <UsageBar value={proc.cpu} max={maxCpu} className="w-16" />
                  </div>
                </td>
                <td className="px-3 py-2">
                  <div className="flex items-center gap-2">
                    <span className="w-16 shrink-0 text-right tabular-nums text-foreground">
                      {proc.memory} MB
                    </span>
                    <UsageBar value={proc.memory} max={maxMemory} className="w-16" />
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </SectionCard>
  );
}
