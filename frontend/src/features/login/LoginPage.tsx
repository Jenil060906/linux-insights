import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Activity } from "lucide-react";
import { motion } from "framer-motion";
import { Card } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { SearchingIndicator } from "@/features/login/components/SearchingIndicator";
import { ServerDiscoveryList } from "@/features/login/components/ServerDiscoveryList";
import { ManualConnectForm } from "@/features/login/components/ManualConnectForm";
import { discoveredServers } from "@/features/login/data/discoveredServers";
import { setSelectedServer } from "@/features/login/lib/selectedServer";
import type { DiscoveredServer, SelectedServer } from "@/features/login/types";

// Server-selection screen shown before the dashboard. No auth, no networking:
// "discovery" is a static list revealed after a short delay, and "connect"
// just persists the chosen server to localStorage before navigating on.
export function LoginPage() {
  const navigate = useNavigate();
  const [serversRevealed, setServersRevealed] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setServersRevealed(true), 900);
    return () => clearTimeout(timer);
  }, []);

  function connect(server: SelectedServer) {
    setSelectedServer(server);
    navigate("/dashboard", { replace: true });
  }

  function handleDiscoveredConnect(server: DiscoveredServer) {
    connect({
      hostname: server.hostname,
      os: server.os,
      status: server.status,
      source: "discovered",
      connectedAt: new Date().toISOString(),
    });
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-background px-4 py-16">
      {/* Branding */}
      <motion.div
        initial={{ opacity: 0, y: -8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: "easeOut" }}
        className="mb-8 flex flex-col items-center text-center"
      >
        <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-lg bg-primary">
          <Activity aria-hidden="true" className="h-6 w-6 text-primary-foreground" strokeWidth={2.5} />
        </div>
        <h1 className="text-2xl font-bold tracking-tight text-foreground">Linux Insight</h1>
        <p className="mt-1.5 text-sm text-muted-foreground">
          Intelligent Linux Observability Platform
        </p>
      </motion.div>

      {/* Center card */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.45, delay: 0.1, ease: "easeOut" }}
        className="w-full max-w-lg"
      >
        <Card className="p-6 shadow-soft">
          <SearchingIndicator />

          <div className="mt-4">
            <p className="mb-2 text-2xs font-medium uppercase tracking-wide text-muted-foreground">
              Available Servers
            </p>
            <ServerDiscoveryList
              servers={discoveredServers}
              revealed={serversRevealed}
              onConnect={handleDiscoveredConnect}
            />
          </div>

          <Separator className="my-5" />

          <ManualConnectForm onConnect={connect} />
        </Card>
      </motion.div>
    </div>
  );
}
