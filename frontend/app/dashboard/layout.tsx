import type { ReactNode } from "react";

import { RequireAuth } from "@/components/auth/require-auth";
import { PageContainer } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/ui/page-header";
import { DashboardNav } from "@/features/dashboard/dashboard-nav";

export default function DashboardLayout({
  children,
}: {
  children: ReactNode;
}) {
  return (
    <RequireAuth roles={["admin", "barber"]}>
      <PageContainer>
        <PageHeader
          description="Información operativa calculada sobre los turnos reales."
          eyebrow="Panel interno"
          title="Panel"
        />
        <div className="mt-5">
          <DashboardNav />
        </div>
        <div className="mt-5">{children}</div>
      </PageContainer>
    </RequireAuth>
  );
}
