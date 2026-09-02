"use client";

import type { FormEvent } from "react";

import { Button } from "@/components/ui/button";
import { InputField } from "@/components/ui/field";
import { FormMessage } from "@/components/ui/states";
import { useAuthSubmit } from "@/features/auth/use-auth-mutation";
import { register } from "@/services/auth";

export function RegisterForm() {
  const { submit, isSubmitting, message, fieldErrors } = useAuthSubmit();

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);

    void submit(() =>
      register({
        email: String(data.get("email") ?? ""),
        password: String(data.get("password") ?? ""),
        full_name: String(data.get("fullName") ?? "") || undefined,
        phone: String(data.get("phone") ?? "") || undefined,
      }),
    );
  }

  return (
    <form className="space-y-4" noValidate onSubmit={handleSubmit}>
      <InputField
        autoComplete="name"
        error={fieldErrors.full_name}
        label="Nombre y apellido"
        name="fullName"
        placeholder="Tu nombre"
        required
      />
      <InputField
        autoComplete="email"
        error={fieldErrors.email}
        label="Email"
        name="email"
        placeholder="tu@email.com"
        required
        type="email"
      />
      <InputField
        autoComplete="tel"
        error={fieldErrors.phone}
        hint="Lo usamos solo para avisarte por un cambio de turno."
        label="Telefono (opcional)"
        name="phone"
        type="tel"
      />
      <InputField
        autoComplete="new-password"
        error={fieldErrors.password}
        hint="Minimo 8 caracteres."
        label="Contrasena"
        minLength={8}
        name="password"
        required
        type="password"
      />
      {message ? <FormMessage tone="error">{message}</FormMessage> : null}
      <Button className="w-full" isLoading={isSubmitting} type="submit">
        {isSubmitting ? "Creando cuenta..." : "Crear cuenta"}
      </Button>
    </form>
  );
}
