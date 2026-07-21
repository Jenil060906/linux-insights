import { useId, useState, type FormEvent } from "react";
import { ChevronDown } from "lucide-react";
import { AnimatePresence, motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import type { SelectedServer } from "@/features/login/types";

interface ManualConnectFormProps {
  onConnect: (server: SelectedServer) => void;
}

const DEFAULT_PORT = "8000";

// Fallback path for a server the discovery list didn't find. No networking —
// submitting just builds a SelectedServer from whatever was typed in.
export function ManualConnectForm({ onConnect }: ManualConnectFormProps) {
  const [serverName, setServerName] = useState("");
  const [ip, setIp] = useState("");
  const [port, setPort] = useState(DEFAULT_PORT);
  const [advancedOpen, setAdvancedOpen] = useState(false);

  const nameId = useId();
  const ipId = useId();
  const portId = useId();
  const advancedFieldsId = useId();

  const trimmedName = serverName.trim();

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!trimmedName) return;

    onConnect({
      hostname: trimmedName,
      os: "Linux",
      status: "healthy",
      ip: ip.trim() || undefined,
      port: port.trim() ? Number(port) : undefined,
      source: "manual",
      connectedAt: new Date().toISOString(),
    });
  }

  return (
    <div>
      <p className="mb-3 text-sm font-medium text-foreground">Can&apos;t find your server?</p>

      <form onSubmit={handleSubmit} className="flex flex-col gap-3">
        <div>
          <label htmlFor={nameId} className="mb-1.5 block text-xs font-medium text-muted-foreground">
            Server Name
          </label>
          <Input
            id={nameId}
            placeholder="e.g. ubuntu-staging-02"
            value={serverName}
            onChange={(event) => setServerName(event.target.value)}
          />
        </div>

        <button
          type="button"
          onClick={() => setAdvancedOpen((open) => !open)}
          aria-expanded={advancedOpen}
          aria-controls={advancedFieldsId}
          className="flex w-fit items-center gap-1.5 text-xs font-medium text-muted-foreground transition-colors hover:text-foreground"
        >
          Advanced
          <motion.span
            animate={{ rotate: advancedOpen ? 180 : 0 }}
            transition={{ duration: 0.2 }}
            className="flex"
          >
            <ChevronDown aria-hidden="true" className="h-3.5 w-3.5" />
          </motion.span>
        </button>

        <AnimatePresence initial={false}>
          {advancedOpen && (
            <motion.div
              key="advanced-fields"
              id={advancedFieldsId}
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.2, ease: "easeInOut" }}
              className="overflow-hidden"
            >
              <div className="flex flex-col gap-3 pt-0.5">
                <div>
                  <label htmlFor={ipId} className="mb-1.5 block text-xs font-medium text-muted-foreground">
                    IP Address
                  </label>
                  <Input
                    id={ipId}
                    placeholder="192.168.1.42"
                    value={ip}
                    onChange={(event) => setIp(event.target.value)}
                  />
                </div>
                <div>
                  <label htmlFor={portId} className="mb-1.5 block text-xs font-medium text-muted-foreground">
                    Port
                  </label>
                  <Input
                    id={portId}
                    type="number"
                    inputMode="numeric"
                    value={port}
                    onChange={(event) => setPort(event.target.value)}
                  />
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        <Button type="submit" variant="outline" className="mt-1 w-full" disabled={!trimmedName}>
          Connect Manually
        </Button>
      </form>
    </div>
  );
}
