import type { Metadata } from "next";

import { RequireAuth } from "@/components/auth/require-auth";
import { PageContainer } from "@/components/layout/app-shell";
import { PageHeader } from "@/components/ui/page-header";
import { ProfileForm } from "@/features/profile/profile-form";

export const metadata: Metadata = { title: "Mi perfil" };

export default function ProfilePage() {
  return (
    <RequireAuth>
      <PageContainer>
        <PageHeader eyebrow="Cuenta" title="Mi perfil" />
        <div className="mt-6 max-w-xl">
          <ProfileForm />
        </div>
      </PageContainer>
    </RequireAuth>
  );
}
