import type { Metadata } from "next";

import { RequireAuth } from "@/components/auth/require-auth";
import { PageContainer } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/ui/page-header";
import { AppointmentDetail } from "@/features/appointments/appointment-detail";

export const metadata: Metadata = { title: "Detalle del turno" };

export default async function AppointmentDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;

  return (
    <RequireAuth>
      <PageContainer>
        <PageHeader eyebrow="Turno" title="Detalle del turno" />
        <div className="mt-6 max-w-3xl">
          <AppointmentDetail appointmentId={id} />
        </div>
      </PageContainer>
    </RequireAuth>
  );
}
