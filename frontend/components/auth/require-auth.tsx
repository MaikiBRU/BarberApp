"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";
import type { ReactNode } from "react";

import { SkeletonRows } from "@/components/ui/states";
import { useSession } from "@/hooks/use-session";
import { routes } from "@/lib/routes";
import type { UserRole } from "@/types/domain";

type RequireAuthProps = {
  children: ReactNode;
  roles?: UserRole[];
};

/**
 * Client-side gate for routes that need a session.
 *
 * This is a navigation convenience only. Every protected read and write
 * is authorized again by the API, so bypassing this component reveals
 * nothing.
 */
export function RequireAuth({ children, roles }: RequireAuthProps) {
  const router = useRouter();
  const { isReady, isAuthenticated, user } = useSession();

  const isAllowed =
    isAuthenticated && (!roles || (user ? roles.includes(user.role) : false));

  useEffect(() => {
    if (!isReady) {
      return;
    }
    if (!isAuthenticated) {
      router.replace(routes.login);
      return;
    }
    if (!isAllowed) {
      router.replace(routes.home);
    }
  }, [isAllowed, isAuthenticated, isReady, router]);

  if (!isReady || !isAllowed) {
    return (
      <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6 lg:px-8">
        <SkeletonRows rows={3} />
      </div>
    );
  }

  return <>{children}</>;
}
