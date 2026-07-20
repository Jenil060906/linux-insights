import { AnimatePresence, motion } from "framer-motion";
import { Skeleton } from "@/components/ui/skeleton";
import { DiscoveredServerCard } from "@/features/login/components/DiscoveredServerCard";
import type { DiscoveredServer } from "@/features/login/types";

interface ServerDiscoveryListProps {
  servers: DiscoveredServer[];
  revealed: boolean;
  onConnect: (server: DiscoveredServer) => void;
}

// Crossfades from a row-shaped skeleton to the real (dummy) results — the
// same "loading skeleton, not a spinner" language the dashboard uses for
// its one real async boundary, reused here for a purely presentational
// reveal delay (there's no actual scan to wait on).
export function ServerDiscoveryList({ servers, revealed, onConnect }: ServerDiscoveryListProps) {
  return (
    <div aria-live="polite">
      <AnimatePresence mode="wait" initial={false}>
        {revealed ? (
          <motion.div
            key="results"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="flex flex-col gap-2"
          >
            {servers.map((server, i) => (
              <motion.div
                key={server.id}
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: i * 0.08 }}
              >
                <DiscoveredServerCard server={server} onConnect={onConnect} />
              </motion.div>
            ))}
          </motion.div>
        ) : (
          <motion.div
            key="skeleton"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="flex flex-col gap-2"
          >
            <Skeleton className="h-[60px]" />
            <Skeleton className="h-[60px]" />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
