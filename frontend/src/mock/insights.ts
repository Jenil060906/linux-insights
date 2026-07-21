// Mock data layer — "AI insights" domain. See server.ts for the function-vs-constant rationale.
// Not one of the five domains named in the original request, but added for
// full coverage: every dashboard section's data now lives under src/mock/,
// rather than splitting some data here and leaving the rest in the old
// single-file data/placeholder.ts.
import type { AIInsight } from "@/types/system";

const aiInsights: AIInsight[] = [
  {
    id: "insight-1",
    category: "performance",
    impact: "medium",
    title: "Memory usage trending upward over 7 days",
    description:
      "Node process memory has grown ~8% week-over-week. Likely candidate: a slow leak in the request cache layer.",
    timestamp: "10 min ago",
  },
  {
    id: "insight-2",
    category: "security",
    impact: "high",
    title: "Unusual SSH access pattern detected",
    description:
      "Login attempts from a new geographic region were correlated with the auth-monitor alert. Recommend reviewing recent sessions.",
    timestamp: "1 hour ago",
  },
  {
    id: "insight-3",
    category: "cost",
    impact: "low",
    title: "Disk headroom sufficient for 40+ days",
    description:
      "At current growth rate, /var will not reach capacity for at least 40 days — no immediate action needed.",
    timestamp: "3 hours ago",
  },
];

/** Mirrors GET /api/insights */
export function getAiInsights(): AIInsight[] {
  return aiInsights;
}
