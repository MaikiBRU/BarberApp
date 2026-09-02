"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { useSession } from "@/hooks/use-session";
import { cn } from "@/lib/cn";
import { routes } from "@/lib/routes";

const staffLinks = [
  { href: routes.dashboard, label: "Resumen" },
  { href: routes.dashboardAppointments, label: "Turnos" },
];

const adminLinks = [
  { href: routes.dashboardServices, label: "Servicios" },
  { href: routes.dashboardExtras, label: "Extras" },
  { href: routes.dashboardBarbers, label: "Barberos" },
  { href: routes.dashboardHours, label: "Horarios" },
];

export function DashboardNav() {
  const pathname = usePathname();
  const { isAdmin } = useSession();
  const links = isAdmin ? [...staffLinks, ...adminLinks] : staffLinks;

  return (
    <nav
      aria-label="Secciones del panel"
      className="-mx-4 overflow-x-auto px-4 sm:mx-0 sm:px-0"
    >
      <ul className="flex min-w-max gap-1 border-b border-line">
        {links.map((link) => {
          const isActive = pathname === link.href;
          return (
            <li key={link.href}>
              <Link
                aria-current={isActive ? "page" : undefined}
                className={cn(
                  "-mb-px block border-b-2 px-3 py-2.5 text-sm font-medium transition-colors",
                  isActive
                    ? "border-brand text-ink"
                    : "border-transparent text-ink-muted hover:text-ink",
                )}
                href={link.href}
              >
                {link.label}
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
