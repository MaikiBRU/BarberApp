import { create } from "zustand";

import type { UserRole } from "@/types/domain";

export type SessionUser = {
  id: string;
  email: string;
  role: UserRole;
};

type StoredSession = {
  token: string;
  user: SessionUser;
  expiresAt: number;
};

type SessionState = {
  token: string | null;
  user: SessionUser | null;
  /** False until the first hydration attempt has finished. */
  isReady: boolean;
  setSession: (token: string, user: SessionUser, expiresIn: number) => void;
  clearSession: () => void;
  hydrate: () => void;
};

const STORAGE_KEY = "barberapp.session";

function readStoredSession(): StoredSession | null {
  if (typeof window === "undefined") {
    return null;
  }

  const raw = window.localStorage.getItem(STORAGE_KEY);
  if (!raw) {
    return null;
  }

  try {
    const parsed = JSON.parse(raw) as StoredSession;
    if (
      typeof parsed?.token !== "string" ||
      typeof parsed?.expiresAt !== "number" ||
      !parsed?.user?.id
    ) {
      throw new Error("malformed session");
    }
    if (parsed.expiresAt <= Date.now()) {
      window.localStorage.removeItem(STORAGE_KEY);
      return null;
    }
    return parsed;
  } catch {
    window.localStorage.removeItem(STORAGE_KEY);
    return null;
  }
}

export const useSessionStore = create<SessionState>((set) => ({
  token: null,
  user: null,
  isReady: false,

  setSession: (token, user, expiresIn) => {
    const expiresAt = Date.now() + expiresIn * 1000;
    if (typeof window !== "undefined") {
      window.localStorage.setItem(
        STORAGE_KEY,
        JSON.stringify({ token, user, expiresAt }),
      );
    }
    set({ token, user, isReady: true });
  },

  clearSession: () => {
    if (typeof window !== "undefined") {
      window.localStorage.removeItem(STORAGE_KEY);
    }
    set({ token: null, user: null, isReady: true });
  },

  hydrate: () => {
    const stored = readStoredSession();
    set({
      token: stored?.token ?? null,
      user: stored?.user ?? null,
      isReady: true,
    });
  },
}));

export const sessionStorageKey = STORAGE_KEY;
