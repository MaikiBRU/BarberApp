import type { Metadata } from "next";

import { AppointmentsBoard } from "@/features/dashboard/appointments-board";

export const metadata: Metadata = { title: "Turnos" };

export default function DashboardAppointmentsPage() {
  return <AppointmentsBoard />;
}
