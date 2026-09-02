import type { Metadata } from "next";

import { PageContainer } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/ui/page-header";
import { BookingFlow } from "@/features/booking/booking-flow";

export const metadata: Metadata = { title: "Reservar turno" };

export default function BookingPage() {
  return (
    <PageContainer>
      <PageHeader
        description="Elegi servicio, barbero y horario. Los turnos que ves son los que realmente estan libres."
        eyebrow="Reserva"
        title="Reservar turno"
      />
      <div className="mt-6 max-w-3xl">
        <BookingFlow />
      </div>
    </PageContainer>
  );
}
