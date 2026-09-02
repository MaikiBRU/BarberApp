import type { Metadata } from "next";

import { RequireAuth } from "@/components/auth/require-auth";
import { ServiceManager } from "@/features/dashboard/service-manager";

export const metadata: Metadata = { title: "Servicios" };

export default function DashboardServicesPage() {
  return (
    <RequireAuth roles={["admin"]}>
      <ServiceManager />
    </RequireAuth>
  );
}
