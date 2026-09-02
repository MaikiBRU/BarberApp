import type { Metadata } from "next";

import { RequireAuth } from "@/components/auth/require-auth";
import { BarberManager } from "@/features/dashboard/barber-manager";

export const metadata: Metadata = { title: "Barberos" };

export default function DashboardBarbersPage() {
  return (
    <RequireAuth roles={["admin"]}>
      <BarberManager />
    </RequireAuth>
  );
}
