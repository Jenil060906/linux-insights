import { Loader2 } from "lucide-react";

// Continuous "still scanning" affordance shown above the results — the scan
// never really completes (no networking), it's a permanent ambient state
// that keeps the flow feeling live while dummy results sit below it.
export function SearchingIndicator() {
  return (
    <div className="flex items-center gap-2 text-xs font-medium text-muted-foreground">
      <Loader2 aria-hidden="true" className="h-3.5 w-3.5 text-primary motion-safe:animate-spin" />
      <span>Searching for Linux servers…</span>
    </div>
  );
}
