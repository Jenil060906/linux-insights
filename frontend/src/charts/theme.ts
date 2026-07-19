// Recharts consumes raw color values (SVG attributes), not Tailwind classes.
// These mirror the design tokens in tailwind.config.ts — keep in sync if the palette changes.
export const chartTheme = {
  border: "#30363D",
  mutedForeground: "#9CA3AF",
  primary: "#3B82F6",
  success: "#22C55E",
  warning: "#F59E0B",
  danger: "#EF4444",
} as const;
