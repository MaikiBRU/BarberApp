"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useState } from "react";

import { Button, LinkButton } from "@/components/ui/button";
import { useSession } from "@/hooks/use-session";
import { cn } from "@/lib/cn";
import { shopConfig } from "@/lib/config";
import { routes } from "@/lib/routes";

type NavItem = {
  href: string;
  label: string;
};

const customerNav: NavItem[] = [
  { href: routes.booking, label: "Reservar" },
  { href: routes.appointments, label: "Mis turnos" },
  { href: routes.profile, label: "Perfil" },
];

const staffNav: NavItem[] = [
  { href: routes.dashboard, label: "Panel" },
  { href: routes.dashboardAppointments, label: "Turnos" },
];

const adminNav: NavItem[] = [
  { href: routes.dashboardServices, label: "Servicios" },
  { href: routes.dashboardBarbers, label: "Barberos" },
];

export function SiteHeader() {
  const pathname = usePathname();
  const router = useRouter();
  const { isReady, isAuthenticated, isStaff, isAdmin, user, signOut } =
    useSession();
  const [isMenuOpen, setMenuOpen] = useState(false);

  const items = isStaff
    ? [...staffNav, ...(isAdmin ? adminNav : [])]
    : customerNav;

  function handleSignOut() {
    signOut();
    setMenuOpen(false);
    router.push(routes.home);
  }

  return (
    <header className="sticky top-0 z-20 border-b border-line bg-surface/95 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-3 sm:px-6 lg:px-8">
        <Link
          className="text-lg font-semibold tracking-tight"
          href={routes.home}
        >
          {shopConfig.name}
        </Link>

        <nav
          aria-label="Principal"
          className="hidden items-center gap-1 md:flex"
        >
          {isReady && isAuthenticated
            ? items.map((item) => (
                <Link
                  className={cn(
                    "rounded-md px-3 py-2 text-sm font-medium transition-colors",
                    pathname === item.href
                      ? "bg-surface-muted text-ink"
                      : "text-ink-muted hover:text-ink",
                  )}
                  href={item.href}
                  key={item.href}
                >
                  {item.label}
                </Link>
              ))
            : null}
        </nav>

        <div className="hidden items-center gap-2 md:flex">
          {!isReady ? (
            <span className="h-9 w-24 animate-pulse rounded-md bg-surface-muted" />
          ) : isAuthenticated ? (
            <>
              <span className="max-w-40 truncate text-sm text-ink-muted">
                {user?.email}
              </span>
              <Button onClick={handleSignOut} size="sm" variant="secondary">
                Salir
              </Button>
            </>
          ) : (
            <>
              <LinkButton href={routes.demo} size="sm" variant="ghost">
                Ver demo
              </LinkButton>
              <LinkButton href={routes.login} size="sm" variant="secondary">
                Entrar
              </LinkButton>
              <LinkButton href={routes.register} size="sm">
                Crear cuenta
              </LinkButton>
            </>
          )}
        </div>

        <Button
          aria-controls="mobile-nav"
          aria-expanded={isMenuOpen}
          className="md:hidden"
          onClick={() => setMenuOpen((open) => !open)}
          size="sm"
          variant="secondary"
        >
          {isMenuOpen ? "Cerrar" : "Menu"}
        </Button>
      </div>

      {isMenuOpen ? (
        <div
          className="border-t border-line bg-surface px-4 py-3 md:hidden"
          id="mobile-nav"
        >
          <nav aria-label="Principal movil" className="flex flex-col gap-1">
            {isReady && isAuthenticated
              ? items.map((item) => (
                  <Link
                    className="rounded-md px-3 py-2.5 text-sm font-medium text-ink-muted hover:bg-surface-muted hover:text-ink"
                    href={item.href}
                    key={item.href}
                    onClick={() => setMenuOpen(false)}
                  >
                    {item.label}
                  </Link>
                ))
              : null}
          </nav>
          <div className="mt-3 flex flex-col gap-2 border-t border-line pt-3">
            {isAuthenticated ? (
              <Button onClick={handleSignOut} variant="secondary">
                Salir
              </Button>
            ) : (
              <>
                <LinkButton href={routes.demo} variant="secondary">
                  Ver demo
                </LinkButton>
                <LinkButton href={routes.login} variant="secondary">
                  Entrar
                </LinkButton>
                <LinkButton href={routes.register}>Crear cuenta</LinkButton>
              </>
            )}
          </div>
        </div>
      ) : null}
    </header>
  );
}
