"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useCallback, useEffect, useState } from "react";

import {
  readDemoSession,
  resetDemoSession,
  switchDemoRole,
} from "@/services/demo";
import { useSessionStore } from "@/store/session-store";
import type { DemoStartResponse, UserRole } from "@/types/domain";

const POLL_MS = 30_000;

/**
 * Live sandbox state for the demo chrome.
 *
 * The poll doubles as the keep-alive: every read refreshes the idle
 * timer server-side, so a visitor reading a dashboard is not dropped
 * mid-sentence. The countdown is derived from the expiry instant and a
 * ticking clock rather than mirrored into state, so nothing has to be
 * re-synchronised when the poll returns.
 */
export function useDemoSession(enabled: boolean) {
  const token = useSessionStore((state) => state.token);
  const setSession = useSessionStore((state) => state.setSession);
  const queryClient = useQueryClient();
  const [now, setNow] = useState(() => Date.now());

  const query = useQuery({
    queryKey: ["demo", "session"],
    queryFn: () => readDemoSession(token as string),
    enabled: enabled && Boolean(token),
    refetchInterval: POLL_MS,
    retry: false,
  });

  useEffect(() => {
    if (!enabled) return;
    const tick = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(tick);
  }, [enabled]);

  const adopt = useCallback(
    (payload: DemoStartResponse) => {
      setSession(
        payload.access_token,
        {
          id: payload.user.id,
          email: payload.user.email,
          role: payload.user.role,
        },
        payload.expires_in,
        { isDemo: true },
      );
      queryClient.setQueryData(["demo", "session"], payload.session);
      void queryClient.invalidateQueries({ queryKey: ["appointments"] });
      void queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      void queryClient.invalidateQueries({ queryKey: ["availability"] });
    },
    [queryClient, setSession],
  );

  const roleMutation = useMutation({
    mutationFn: (role: UserRole) => switchDemoRole(token as string, role),
    onSuccess: adopt,
  });

  const resetMutation = useMutation({
    mutationFn: () => resetDemoSession(token as string),
    onSuccess: (payload) => {
      adopt(payload);
      void queryClient.invalidateQueries({ queryKey: ["services"] });
      void queryClient.invalidateQueries({ queryKey: ["extras"] });
      void queryClient.invalidateQueries({ queryKey: ["barbers"] });
      void queryClient.invalidateQueries({ queryKey: ["business-hours"] });
    },
  });

  const expiresAt = query.data
    ? new Date(query.data.state.expires_at).getTime()
    : 0;
  const seconds = expiresAt
    ? Math.max(Math.floor((expiresAt - now) / 1000), 0)
    : 0;

  return {
    session: query.data ?? null,
    seconds,
    isExpired: query.isError,
    changeRole: (role: UserRole) => roleMutation.mutateAsync(role),
    reset: () => resetMutation.mutateAsync(),
  };
}
