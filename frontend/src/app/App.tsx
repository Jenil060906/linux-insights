import { MotionConfig } from "framer-motion";
import { BrowserRouter, Navigate, Route, Routes, useNavigate } from "react-router-dom";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { DashboardPage } from "@/pages/DashboardPage";
import { LoginPage } from "@/features/login/LoginPage";
import { clearSelectedServer, getSelectedServer } from "@/features/login/lib/selectedServer";
import type { HostInfo } from "@/types/system";

// "/" — login/server-selection. If a server was already chosen (localStorage
// has one), skip straight to the dashboard instead of showing the picker again.
function LoginRoute() {
  if (getSelectedServer()) {
    return <Navigate to="/dashboard" replace />;
  }
  return <LoginPage />;
}

// "/dashboard" — guarded the other way: no selected server means there's
// nothing to show, so bounce back to login. The selected server is mapped
// into the dashboard's own HostInfo shape here, at the route boundary —
// this is the one place the two features touch.
function DashboardRoute() {
  const navigate = useNavigate();
  const selected = getSelectedServer();
  if (!selected) {
    return <Navigate to="/" replace />;
  }

  const host: HostInfo = {
    hostname: selected.hostname,
    os: selected.os,
    connectionStatus: "connected",
    lastSyncedAt: "Just now",
    latencyMs: 14,
  };

  function handleLogout() {
    clearSelectedServer();
    navigate("/", { replace: true });
  }

  return (
    <DashboardLayout host={host} onLogout={handleLogout}>
      <DashboardPage />
    </DashboardLayout>
  );
}

function App() {
  return (
    <MotionConfig reducedMotion="user">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<LoginRoute />} />
          <Route path="/dashboard" element={<DashboardRoute />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </MotionConfig>
  );
}

export default App;
