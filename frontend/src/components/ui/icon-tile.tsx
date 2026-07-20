import type { LucideIcon } from "lucide-react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

// The "icon in a small rounded box" mark used next to every section title,
// stat, insight row, and quick action. Extracted because five components
// independently hand-rolled this exact box before this file existed —
// same idea, five slightly different className strings to keep in sync.
//
// Two tone families, matching the two visual patterns already in use —
// kept as separate, non-overlapping names so "primary" can't mean two
// different renderings depending on which file you're reading:
//  - "neutral"/"accent" — bordered, on the flat `surface` token. Used when
//    the icon sits directly on a Card (which is one step lighter than
//    surface, so this reads as a subtle recessed chip). Purely decorative —
//    no status implied. "accent" tints the icon itself brand-blue; "neutral"
//    keeps it muted gray for a quieter, secondary mark.
//  - "primary"/"success"/"warning"/"danger" — a borderless tint of that
//    color (bg-{color}/10, text-{color}). Reserved for when the icon is
//    communicating live state (e.g. "AI Status", "Uptime"), never used
//    decoratively — see the color-token comment in tailwind.config.ts.
const iconTileVariants = cva(
  "flex shrink-0 items-center justify-center rounded-sm [&_svg]:h-4 [&_svg]:w-4",
  {
    variants: {
      tone: {
        neutral: "border border-border bg-surface text-muted-foreground",
        accent: "border border-border bg-surface text-primary",
        primary: "bg-primary/10 text-primary",
        success: "bg-success/10 text-success",
        warning: "bg-warning/10 text-warning",
        danger: "bg-danger/10 text-danger",
      },
      size: {
        sm: "h-7 w-7",
        md: "h-8 w-8",
        lg: "h-9 w-9",
      },
    },
    defaultVariants: {
      tone: "neutral",
      size: "sm",
    },
  }
);

export interface IconTileProps extends VariantProps<typeof iconTileVariants> {
  icon: LucideIcon;
  className?: string;
}

export function IconTile({ icon: Icon, tone, size, className }: IconTileProps) {
  return (
    <div className={cn(iconTileVariants({ tone, size }), className)}>
      <Icon aria-hidden="true" />
    </div>
  );
}
