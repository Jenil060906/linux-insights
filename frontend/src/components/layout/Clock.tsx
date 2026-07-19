import { useEffect, useState } from "react";

// Isolated so its per-second tick only re-renders this component, not the whole Header.
export function Clock() {
  const [now, setNow] = useState(() => new Date());

  useEffect(() => {
    const interval = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(interval);
  }, []);

  const timeString = now.toLocaleTimeString("en-US", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  });

  return (
    <span className="hidden font-mono text-xs tabular-nums text-muted-foreground lg:block">
      <time dateTime={now.toISOString()}>{timeString}</time>
    </span>
  );
}
