import { beforeEach, describe, expect, it } from "vitest";

import { sessionStorageKey, useSessionStore } from "@/store/session-store";

const user = {
  id: "u-1",
  email: "cliente@example.com",
  role: "customer" as const,
};

beforeEach(() => {
  window.localStorage.clear();
  useSessionStore.setState({ token: null, user: null, isReady: false });
});

describe("session store", () => {
  it("persists a session and restores it on hydrate", () => {
    useSessionStore.getState().setSession("token-abc", user, 3600);
    useSessionStore.setState({ token: null, user: null, isReady: false });

    useSessionStore.getState().hydrate();

    expect(useSessionStore.getState().token).toBe("token-abc");
    expect(useSessionStore.getState().user?.email).toBe(user.email);
    expect(useSessionStore.getState().isReady).toBe(true);
  });

  it("discards a session whose token has already expired", () => {
    window.localStorage.setItem(
      sessionStorageKey,
      JSON.stringify({
        token: "stale",
        user,
        expiresAt: Date.now() - 1000,
      }),
    );

    useSessionStore.getState().hydrate();

    expect(useSessionStore.getState().token).toBeNull();
    expect(window.localStorage.getItem(sessionStorageKey)).toBeNull();
  });

  it("discards malformed stored data instead of crashing", () => {
    window.localStorage.setItem(sessionStorageKey, "not-json");

    useSessionStore.getState().hydrate();

    expect(useSessionStore.getState().token).toBeNull();
    expect(useSessionStore.getState().isReady).toBe(true);
  });

  it("clears storage on sign out", () => {
    useSessionStore.getState().setSession("token-abc", user, 3600);

    useSessionStore.getState().clearSession();

    expect(useSessionStore.getState().user).toBeNull();
    expect(window.localStorage.getItem(sessionStorageKey)).toBeNull();
  });
});
