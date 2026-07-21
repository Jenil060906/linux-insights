import { useState } from "react";

export type CategoryFilter<K extends string> = "all" | K;

interface UseCategoryFilterResult<TItem, K extends string> {
  filter: CategoryFilter<K>;
  setFilter: (filter: CategoryFilter<K>) => void;
  counts: Record<CategoryFilter<K>, number>;
  visibleItems: TItem[];
}

// Shared "all / by-category" filter behavior used by every filterable list in
// the dashboard (Alerts by severity, Logs by level): tracks the active
// filter, derives per-category counts (plus a synthetic "all"), and the
// resulting filtered list — previously hand-rolled, near-identically, in
// each section.
export function useCategoryFilter<TItem, K extends string>(
  items: TItem[],
  getCategory: (item: TItem) => K,
  categories: readonly K[]
): UseCategoryFilterResult<TItem, K> {
  const [filter, setFilter] = useState<CategoryFilter<K>>("all");

  const counts = { all: items.length } as Record<CategoryFilter<K>, number>;
  for (const key of categories) counts[key] = 0;
  for (const item of items) counts[getCategory(item)] += 1;

  const visibleItems = filter === "all" ? items : items.filter((item) => getCategory(item) === filter);

  return { filter, setFilter, counts, visibleItems };
}
