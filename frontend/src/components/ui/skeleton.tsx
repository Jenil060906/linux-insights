import { cn } from "@/lib/utils";

function Skeleton({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("rounded-sm bg-surface motion-safe:animate-pulse", className)}
      {...props}
    />
  );
}

export { Skeleton };
