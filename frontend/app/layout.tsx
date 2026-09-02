import type { Metadata, Viewport } from "next";

import { AppShell } from "@/components/layout/app-shell";
import { shopConfig } from "@/lib/config";

import { Providers } from "./providers";
import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: `${shopConfig.name} | Reservas online`,
    template: `%s | ${shopConfig.name}`,
  },
  description:
    "Reserva tu turno en la barberia, consulta disponibilidad real y gestiona la agenda del local.",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="es">
      <body>
        <a
          className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-md focus:bg-brand focus:px-4 focus:py-2 focus:text-on-brand"
          href="#contenido"
        >
          Saltar al contenido
        </a>
        <Providers>
          <AppShell>
            <div id="contenido">{children}</div>
          </AppShell>
        </Providers>
      </body>
    </html>
  );
}
