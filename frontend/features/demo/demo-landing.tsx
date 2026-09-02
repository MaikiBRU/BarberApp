"use client";

import { useQuery } from "@tanstack/react-query";
import { useRouter, useSearchParams } from "next/navigation";
import { useState } from "react";

import { Card } from "@/components/ui/card";
import { DemoPitch } from "@/features/demo/demo-pitch";
import { DemoStartPanel } from "@/features/demo/demo-start-panel";
import { toMessage } from "@/lib/error-messages";
import { routes } from "@/lib/routes";
import { fetchDemoConfig, startDemoSession } from "@/services/demo";
import { useSessionStore } from "@/store/session-store";

export function DemoLanding() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const setSession = useSessionStore((state) => state.setSession);
  const [isStarting, setStarting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const config = useQuery({
    queryKey: ["demo", "config"],
    queryFn: fetchDemoConfig,
  });

  const notice =
    searchParams.get("motivo") === "expirada"
      ? "Tu sesión de demo expiró. Podés empezar una nueva ahora mismo."
      : null;

  async function begin() {
    setStarting(true);
    setError(null);
    try {
      const payload = await startDemoSession();
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
      router.replace(routes.booking);
      router.refresh();
    } catch (caught) {
      setError(toMessage(caught));
      setStarting(false);
    }
  }

  return (
    <div className="mx-auto grid w-full max-w-6xl items-start gap-6 px-4 py-8 sm:px-6 lg:grid-cols-[1.1fr_0.9fr] lg:px-8">
      <Card className="order-last p-5 sm:p-6 lg:order-none">
        <DemoPitch />
      </Card>

      <Card className="p-5 sm:p-6">
        <DemoStartPanel
          error={error}
          isDisabled={config.isSuccess && !config.data.enabled}
          isLoadingLimits={config.isPending}
          isStarting={isStarting}
          limits={config.data?.limits}
          notice={notice}
          onStart={() => void begin()}
        />
      </Card>
    </div>
  );
}
