import { Skeleton } from "@/components/ui/skeleton";

// Mimics the eventual chart's proportions (baseline + rising bars + axis ticks)
// so the loading state doesn't read as a generic gray box.
const BAR_HEIGHTS = [38, 52, 46, 62, 70, 56, 48, 60, 76, 58, 66, 62];

interface ChartSkeletonProps {
  height?: number;
}

export function ChartSkeleton({ height = 220 }: ChartSkeletonProps) {
  return (
    <div className="flex flex-col gap-2" style={{ height }} aria-hidden="true">
      <div className="flex flex-1 items-end gap-1.5 border-b border-l border-border py-1 pl-1">
        {BAR_HEIGHTS.map((barHeight, i) => (
          <Skeleton key={i} className="flex-1" style={{ height: `${barHeight}%` }} />
        ))}
      </div>
      <div className="flex justify-between px-1">
        <Skeleton className="h-2 w-8" />
        <Skeleton className="h-2 w-8" />
        <Skeleton className="h-2 w-8" />
      </div>
    </div>
  );
}
