import type { Metadata } from "next";
import Link from "next/link";

import { Card } from "@/components/ui/card";
import { RegisterForm } from "@/features/auth/register-form";
import { routes } from "@/lib/routes";

export const metadata: Metadata = { title: "Crear cuenta" };

export default function RegisterPage() {
  return (
    <div className="mx-auto flex w-full max-w-md flex-col justify-center px-4 py-10 sm:px-6 sm:py-16">
      <Card className="p-5 sm:p-6">
        <h1 className="text-2xl font-semibold tracking-tight">
          Crear cuenta
        </h1>
        <p className="mt-1 text-sm text-ink-muted">
          Tarda menos de un minuto y ya podes reservar.
        </p>
        <div className="mt-6">
          <RegisterForm />
        </div>
        <p className="mt-5 text-sm text-ink-muted">
          Ya tenes cuenta?{" "}
          <Link
            className="font-semibold text-accent underline-offset-4 hover:underline"
            href={routes.login}
          >
            Entrar
          </Link>
        </p>
      </Card>
    </div>
  );
}
