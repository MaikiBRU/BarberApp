import type { ReactNode } from "react";

import { DemoBanner } from "@/components/layout/demo-banner";
import { SiteHeader } from "@/components/layout/site-header";
import { shopConfig } from "@/lib/config";

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-dvh flex-col">
      <SiteHeader />
      <DemoBanner />
      <main className="flex-1">{children}</main>
      <footer className="border-t border-line bg-surface">
        <div className="mx-auto max-w-6xl px-4 py-6 text-sm text-ink-muted sm:px-6 lg:px-8">
          {shopConfig.name} &middot; Reservas online
        </div>
      </footer>
    </div>
  );
}

export function PageContainer({ children }: { children: ReactNode }) {
  return (
    <div className="mx-auto w-full max-w-6xl px-4 py-6 sm:px-6 sm:py-8 lg:px-8">
      {children}
    </div>
  );
}
