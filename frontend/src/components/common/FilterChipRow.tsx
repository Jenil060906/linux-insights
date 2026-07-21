import type { LucideIcon } from "lucide-react";
import { Chip } from "@/components/common/Chip";

export interface FilterOption<K extends string> {
  key: K;
  label: string;
  icon?: LucideIcon;
}

interface FilterChipRowProps<K extends string> {
  /** Accessible name for the filter group, e.g. "Filter alerts by severity". */
  groupLabel: string;
  options: FilterOption<K>[];
  active: K;
  counts: Record<K, number>;
  onChange: (key: K) => void;
}

// Shared filter-chip row: every filterable list in the dashboard (Alerts by
// severity, Logs by level) renders one of these above its results, so
// hover/active states and spacing stay pixel-identical across sections.
// Pairs with `useCategoryFilter` for the state/counts behind it.
export function FilterChipRow<K extends string>({
  groupLabel,
  options,
  active,
  counts,
  onChange,
}: FilterChipRowProps<K>) {
  return (
    <div role="group" aria-label={groupLabel} className="mb-4 flex flex-wrap gap-1.5">
      {options.map((option) => (
        <Chip
          key={option.key}
          icon={option.icon}
          active={active === option.key}
          count={counts[option.key]}
          onClick={() => onChange(option.key)}
        >
          {option.label}
        </Chip>
      ))}
    </div>
  );
}
