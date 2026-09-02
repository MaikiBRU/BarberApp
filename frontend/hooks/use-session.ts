"use client";

import { useEffect } from "react";

import { useSessionStore } from "@/store/session-store";

/**
 * Read the session, hydrating it from storage on first mount.
 *
 * `isReady` stays false during the server render and the first client
 * paint, which lets guarded screens show a loading state instead of
 * flashing a logged-out layout.
 */
export function useSession() {
  const token = useSessionStore((state) => state.token);
  const user = useSessionStore((state) => state.user);
  const isReady = useSessionStore((state) => state.isReady);
  const hydrate = useSessionStore((state) => state.hydrate);
  const clearSession = useSessionStore((state) => state.clearSession);

  useEffect(() => {
    if (!isReady) {
      hydrate();
    }
  }, [hydrate, isReady]);

  return {
    token,
    user,
    isReady,
    isAuthenticated: Boolean(token && user),
    isStaff: user?.role === "admin" || user?.role === "barber",
    isAdmin: user?.role === "admin",
    signOut: clearSession,
  };
}
