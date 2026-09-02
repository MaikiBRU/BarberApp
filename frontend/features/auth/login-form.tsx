"use client";

import type { FormEvent } from "react";

import { Button } from "@/components/ui/button";
import { InputField } from "@/components/ui/field";
import { FormMessage } from "@/components/ui/states";
import { useAuthSubmit } from "@/features/auth/use-auth-mutation";
import { login } from "@/services/auth";

export function LoginForm() {
  const { submit, isSubmitting, message, fieldErrors } = useAuthSubmit();

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);

    void submit(() =>
      login({
        email: String(data.get("email") ?? ""),
        password: String(data.get("password") ?? ""),
      }),
    );
  }

  return (
    <form className="space-y-4" noValidate onSubmit={handleSubmit}>
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
        autoComplete="current-password"
        error={fieldErrors.password}
        label="Contrasena"
        name="password"
        required
        type="password"
      />
      {message ? <FormMessage tone="error">{message}</FormMessage> : null}
      <Button className="w-full" isLoading={isSubmitting} type="submit">
        {isSubmitting ? "Entrando..." : "Entrar"}
      </Button>
    </form>
  );
}
