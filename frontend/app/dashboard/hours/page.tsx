import type { Metadata } from "next";

import { RequireAuth } from "@/components/auth/require-auth";
import { HoursManager } from "@/features/dashboard/hours-manager";

export const metadata: Metadata = { title: "Horarios" };

export default function DashboardHoursPage() {
  return (
    <RequireAuth roles={["admin"]}>
      <HoursManager />
    </RequireAuth>
  );
}
