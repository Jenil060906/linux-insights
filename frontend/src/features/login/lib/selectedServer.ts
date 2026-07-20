// Persistence for the user's chosen server. This is the ONLY thing that
// stands in for "auth" in this phase: no tokens, no session, just a
// remembered connection target — reading it is how the app decides whether
// to show the login screen or go straight to the dashboard.
import type { SelectedServer } from "@/features/login/types";

const STORAGE_KEY = "linux-insight:selected-server";

export function getSelectedServer(): SelectedServer | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    return JSON.parse(raw) as SelectedServer;
  } catch {
    return null;
  }
}

export function setSelectedServer(server: SelectedServer): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(server));
}

export function clearSelectedServer(): void {
  localStorage.removeItem(STORAGE_KEY);
}
