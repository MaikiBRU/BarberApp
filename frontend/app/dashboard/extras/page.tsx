import type { Metadata } from "next";

import { RequireAuth } from "@/components/auth/require-auth";
import { ExtraManager } from "@/features/dashboard/extra-manager";

export const metadata: Metadata = { title: "Extras" };

export default function DashboardExtrasPage() {
  return (
    <RequireAuth roles={["admin"]}>
      <ExtraManager />
    </RequireAuth>
  );
}
