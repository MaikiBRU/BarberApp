import type { Metadata } from "next";
import Link from "next/link";

import { Card } from "@/components/ui/card";
import { LoginForm } from "@/features/auth/login-form";
import { routes } from "@/lib/routes";

export const metadata: Metadata = { title: "Entrar" };

export default function LoginPage() {
  return (
    <div className="mx-auto flex w-full max-w-md flex-col justify-center px-4 py-10 sm:px-6 sm:py-16">
      <Card className="p-5 sm:p-6">
        <h1 className="text-2xl font-semibold tracking-tight">
          Entrar a tu cuenta
        </h1>
        <p className="mt-1 text-sm text-ink-muted">
          Accede para reservar y gestionar tus turnos.
        </p>
        <div className="mt-6">
          <LoginForm />
        </div>
        <p className="mt-5 text-sm text-ink-muted">
          No tenes cuenta?{" "}
          <Link
            className="font-semibold text-accent underline-offset-4 hover:underline"
            href={routes.register}
          >
            Crear cuenta
          </Link>
        </p>
      </Card>
    </div>
  );
}
