import { cn } from "@/lib/utils";

interface MiniSparklineProps {
  data: number[];
  className?: string;
  strokeClassName?: string;
}

// Lightweight decorative trend line — a visual placeholder, not a data chart.
// Real charting (Recharts) is introduced in a later phase.
export function MiniSparkline({ data, className, strokeClassName }: MiniSparklineProps) {
  const width = 100;
  const height = 32;
  const max = Math.max(...data);
  const min = Math.min(...data);
  const range = max - min || 1;

  const linePoints = data.map((value, i) => {
    const x = (i / (data.length - 1)) * width;
    const y = height - ((value - min) / range) * height;
    return `${x},${y}`;
  });

  // Flat (non-gradient) area wash under the line, per the mark spec: series hue at ~10% opacity.
  const areaPoints = [`0,${height}`, ...linePoints, `${width},${height}`].join(" ");

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      preserveAspectRatio="none"
      className={cn("h-8 w-full", className)}
      aria-hidden="true"
    >
      <polygon points={areaPoints} className="fill-primary/10" stroke="none" />
      <polyline
        points={linePoints.join(" ")}
        fill="none"
        strokeWidth={2}
        strokeLinecap="round"
        strokeLinejoin="round"
        className={cn("stroke-primary", strokeClassName)}
      />
    </svg>
  );
}
