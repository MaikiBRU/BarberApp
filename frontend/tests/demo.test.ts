import { beforeEach, describe, expect, it, vi } from "vitest";

import { formatRemaining } from "@/lib/demo-format";
import { sessionStorageKey, useSessionStore } from "@/store/session-store";

const demoUser = {
  id: "u-demo",
  email: "cliente@abc123.demo.barberapp",
  role: "customer" as const,
};

beforeEach(() => {
  window.localStorage.clear();
  useSessionStore.setState({
    token: null,
    user: null,
    isDemo: false,
    isReady: false,
  });
});

describe("formatRemaining", () => {
  it("pads minutes and seconds under an hour", () => {
    expect(formatRemaining(65)).toBe("01:05");
  });

  it("switches to hours past sixty minutes", () => {
    expect(formatRemaining(3 * 3600 + 7 * 60)).toBe("3 h 07 min");
  });

  it("never renders a negative countdown", () => {
    expect(formatRemaining(-30)).toBe("00:00");
  });
});

describe("session store in demo mode", () => {
  it("remembers that a token belongs to a sandbox", () => {
    useSessionStore
      .getState()
      .setSession("demo-token", demoUser, 2700, { isDemo: true });

    expect(useSessionStore.getState().isDemo).toBe(true);
  });

  it("restores the demo flag on hydrate", () => {
    useSessionStore
      .getState()
      .setSession("demo-token", demoUser, 2700, { isDemo: true });
    useSessionStore.setState({ token: null, user: null, isDemo: false });

    useSessionStore.getState().hydrate();

    expect(useSessionStore.getState().isDemo).toBe(true);
    expect(useSessionStore.getState().token).toBe("demo-token");
  });

  it("treats a real login as a non-demo session", () => {
    useSessionStore.getState().setSession("real-token", demoUser, 3600);

    expect(useSessionStore.getState().isDemo).toBe(false);
  });

  it("drops the demo flag on sign out", () => {
    useSessionStore
      .getState()
      .setSession("demo-token", demoUser, 2700, { isDemo: true });

    useSessionStore.getState().clearSession();

    expect(useSessionStore.getState().isDemo).toBe(false);
    expect(window.localStorage.getItem(sessionStorageKey)).toBeNull();
  });

  it("discards an expired sandbox token", () => {
    window.localStorage.setItem(
      sessionStorageKey,
      JSON.stringify({
        token: "stale",
        user: demoUser,
        expiresAt: Date.now() - 1000,
        isDemo: true,
      }),
    );

    useSessionStore.getState().hydrate();

    expect(useSessionStore.getState().token).toBeNull();
    expect(useSessionStore.getState().isDemo).toBe(false);
  });
});

describe("api client tenant awareness", () => {
  it("attaches the stored session to otherwise public requests", async () => {
    const { apiRequest } = await import("@/lib/api-client");
    window.localStorage.setItem(
      sessionStorageKey,
      JSON.stringify({
        token: "sandbox-token",
        user: demoUser,
        expiresAt: Date.now() + 60_000,
        isDemo: true,
      }),
    );
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve([]),
    });
    vi.stubGlobal("fetch", fetchMock);

    await apiRequest("/api/v1/catalog/services");

    const headers = fetchMock.mock.calls[0][1].headers as Headers;
    expect(headers.get("Authorization")).toBe("Bearer sandbox-token");
    vi.unstubAllGlobals();
  });

  it("sends nothing when the stored session has expired", async () => {
    const { apiRequest } = await import("@/lib/api-client");
    window.localStorage.setItem(
      sessionStorageKey,
      JSON.stringify({
        token: "stale",
        user: demoUser,
        expiresAt: Date.now() - 1000,
        isDemo: true,
      }),
    );
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve([]),
    });
    vi.stubGlobal("fetch", fetchMock);

    await apiRequest("/api/v1/catalog/services");

    const headers = fetchMock.mock.calls[0][1].headers as Headers;
    expect(headers.get("Authorization")).toBeNull();
    vi.unstubAllGlobals();
  });

  it("honours an explicit null token for a deliberately anonymous call", async () => {
    const { apiRequest } = await import("@/lib/api-client");
    window.localStorage.setItem(
      sessionStorageKey,
      JSON.stringify({
        token: "sandbox-token",
        user: demoUser,
        expiresAt: Date.now() + 60_000,
        isDemo: true,
      }),
    );
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve([]),
    });
    vi.stubGlobal("fetch", fetchMock);

    await apiRequest("/api/v1/catalog/services", { token: null });

    const headers = fetchMock.mock.calls[0][1].headers as Headers;
    expect(headers.get("Authorization")).toBeNull();
    vi.unstubAllGlobals();
  });
});
