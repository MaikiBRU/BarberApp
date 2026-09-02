"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { useDemoSession } from "@/features/demo/use-demo-session";
import { useSession } from "@/hooks/use-session";
import { cn } from "@/lib/cn";
import { formatRemaining } from "@/lib/demo-format";
import { toMessage } from "@/lib/error-messages";
import { routes } from "@/lib/routes";
import { endDemoSession } from "@/services/demo";
import type { UserRole } from "@/types/domain";

const LOW_TIME_SECONDS = 5 * 60;

/**
 * Status strip shown only inside a demo sandbox.
 *
 * It states the mode, lets the visitor step into any of the three roles
 * against the same data, and shows what is left of the quota and the
 * clock. Everything else on screen is the real product.
 */
export function DemoBanner() {
  const router = useRouter();
  const { token, isDemo, isReady, user, signOut } = useSession();
  const active = isReady && isDemo && Boolean(token);
  const { session, seconds, isExpired, changeRole, reset } =
    useDemoSession(active);
  const [busy, setBusy] = useState<"role" | "reset" | "end" | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  if (active && isExpired) {
    signOut();
    router.replace(`${routes.demo}?motivo=expirada`);
    return null;
  }

  if (!active || !session) {
    return null;
  }

  const { state, personas } = session;
  const lowTime = seconds > 0 && seconds < LOW_TIME_SECONDS;

  async function run(kind: "role" | "reset" | "end", action: () => Promise<void>) {
    setBusy(kind);
    setMessage(null);
    try {
      await action();
    } catch (error) {
      setMessage(toMessage(error));
    } finally {
      setBusy(null);
    }
  }

  async function handleRole(role: UserRole) {
    if (role === user?.role) return;
    await run("role", async () => {
      await changeRole(role);
      router.replace(role === "customer" ? routes.booking : routes.dashboard);
      router.refresh();
    });
  }

  async function handleEnd() {
    await run("end", async () => {
      try {
        if (token) await endDemoSession(token);
      } finally {
        signOut();
        router.replace(routes.demo);
      }
    });
  }

  return (
    <div className="border-b border-accent/30 bg-accent-soft">
      <div className="mx-auto flex max-w-6xl flex-wrap items-center gap-x-4 gap-y-2 px-4 py-2.5 text-xs sm:px-6 lg:px-8">
        <span className="rounded-full bg-accent px-2.5 py-1 font-semibold text-on-brand">
          Demo
        </span>

        <div
          aria-label="Cambiar de rol"
          className="flex items-center gap-1"
          role="group"
        >
          {personas.map((persona) => (
            <button
              aria-pressed={persona.role === state.active_role}
              className={cn(
                "rounded-md px-2.5 py-1 font-medium transition-colors",
                persona.role === state.active_role
                  ? "bg-brand text-on-brand"
                  : "text-ink-muted hover:text-ink",
              )}
              disabled={busy !== null}
              key={persona.role}
              onClick={() => void handleRole(persona.role)}
              title={persona.description}
              type="button"
            >
              {persona.label}
            </button>
          ))}
        </div>

        <span className="text-ink-muted">
          Turnos {state.appointments_used}/{state.appointments_max}
        </span>
        <span className="text-ink-muted">
          Cambios {state.writes_used}/{state.writes_max}
        </span>
        <span
          className={cn(
            lowTime ? "font-semibold text-danger" : "text-ink-muted",
          )}
          title={`Expira ${new Date(state.expires_at).toLocaleString("es-AR")}`}
        >
          Quedan {formatRemaining(seconds)}
        </span>

        {message ? (
          <span className="font-medium text-danger" role="alert">
            {message}
          </span>
        ) : null}

        <div className="ml-auto flex gap-2">
          <Button
            isLoading={busy === "reset"}
            onClick={() =>
              void run("reset", async () => {
                await reset();
                router.refresh();
              })
            }
            size="sm"
            variant="secondary"
          >
            Reiniciar
          </Button>
          <Button
            isLoading={busy === "end"}
            onClick={() => void handleEnd()}
            size="sm"
            variant="ghost"
          >
            Terminar
          </Button>
        </div>
      </div>
    </div>
  );
}
