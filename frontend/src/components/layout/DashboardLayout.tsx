import type { ReactNode } from "react";
import { Header } from "@/components/layout/Header";
import type { HostInfo } from "@/types/system";

interface DashboardLayoutProps {
  children: ReactNode;
  /** Overrides Header's default placeholder host — e.g. the server chosen at login. */
  host?: HostInfo;
}

// Shell that every dashboard page renders inside: header + scrollable content area.
export function DashboardLayout({ children, host }: DashboardLayoutProps) {
  return (
    <div className="min-h-screen bg-background">
      <Header host={host} />
      <main className="mx-auto max-w-[1440px] px-6 py-6">
        <div className="flex flex-col gap-6">{children}</div>
      </main>
    </div>
  );
}
