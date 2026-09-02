import type { Metadata } from "next";

import { RequireAuth } from "@/components/auth/require-auth";
import { PageContainer } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/ui/page-header";
import { MyAppointments } from "@/features/appointments/my-appointments";

export const metadata: Metadata = { title: "Mis turnos" };

export default function AppointmentsPage() {
  return (
    <RequireAuth>
      <PageContainer>
        <PageHeader
          description="Todo lo que reservaste, con su estado actual."
          eyebrow="Cuenta"
          title="Mis turnos"
        />
        <div className="mt-6 max-w-4xl">
          <MyAppointments />
        </div>
      </PageContainer>
    </RequireAuth>
  );
}
