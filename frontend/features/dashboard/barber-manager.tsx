"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import type { FormEvent } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardHeader } from "@/components/ui/card";
import { InputField, TextareaField } from "@/components/ui/field";
import {
  EmptyState,
  ErrorState,
  FormMessage,
  SkeletonRows,
} from "@/components/ui/states";
import { useSession } from "@/hooks/use-session";
import { toFieldErrors, toMessage } from "@/lib/error-messages";
import {
  createBarber,
  listAllBarbers,
  updateBarber,
} from "@/services/catalog";
import type { BarberInput } from "@/services/catalog";

export function BarberManager() {
  const { token } = useSession();
  const queryClient = useQueryClient();
  const [isFormOpen, setFormOpen] = useState(false);

  const query = useQuery({
    queryKey: ["barbers", "admin"],
    queryFn: () => listAllBarbers(token as string),
    enabled: Boolean(token),
  });

  function invalidate() {
    void queryClient.invalidateQueries({ queryKey: ["barbers"] });
    void queryClient.invalidateQueries({ queryKey: ["availability"] });
    void queryClient.invalidateQueries({ queryKey: ["dashboard"] });
  }

  const create = useMutation({
    mutationFn: (input: BarberInput) => createBarber(token as string, input),
    onSuccess: () => {
      invalidate();
      setFormOpen(false);
    },
  });

  const toggle = useMutation({
    mutationFn: (input: { id: string; is_active: boolean }) =>
      updateBarber(token as string, input.id, { is_active: input.is_active }),
    onSuccess: invalidate,
  });

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    create.mutate({
      email: String(data.get("email") ?? ""),
      password: String(data.get("password") ?? ""),
      display_name: String(data.get("displayName") ?? ""),
      bio: String(data.get("bio") ?? "") || null,
      phone: String(data.get("phone") ?? "") || null,
    });
  }

  const fieldErrors = toFieldErrors(create.error);

  return (
    <Card>
      <CardHeader
        action={
          <Button
            onClick={() => setFormOpen((open) => !open)}
            size="sm"
            variant={isFormOpen ? "ghost" : "primary"}
          >
            {isFormOpen ? "Cancelar" : "Nuevo barbero"}
          </Button>
        }
        description="Un barbero inactivo deja de aparecer en la reserva y no puede ingresar."
        title="Barberos"
      />

      {isFormOpen ? (
        <form
          className="grid gap-4 border-b border-line p-4 sm:grid-cols-2 sm:p-5"
          noValidate
          onSubmit={handleSubmit}
        >
          <InputField
            error={fieldErrors.display_name}
            label="Nombre visible"
            maxLength={120}
            name="displayName"
            required
          />
          <InputField
            error={fieldErrors.email}
            label="Email"
            name="email"
            required
            type="email"
          />
          <InputField
            autoComplete="new-password"
            error={fieldErrors.password}
            hint="Minimo 8 caracteres. El barbero podra cambiarla luego."
            label="Contrasena inicial"
            minLength={8}
            name="password"
            required
            type="password"
          />
          <InputField
            error={fieldErrors.phone}
            label="Telefono"
            maxLength={40}
            name="phone"
            type="tel"
          />
          <div className="sm:col-span-2">
            <TextareaField
              error={fieldErrors.bio}
              label="Descripcion"
              maxLength={1000}
              name="bio"
            />
          </div>
          {create.isError ? (
            <div className="sm:col-span-2">
              <FormMessage tone="error">{toMessage(create.error)}</FormMessage>
            </div>
          ) : null}
          <div className="sm:col-span-2">
            <Button isLoading={create.isPending} type="submit">
              Crear barbero
            </Button>
          </div>
        </form>
      ) : null}

      {query.isPending ? (
        <SkeletonRows rows={2} />
      ) : query.isError ? (
        <ErrorState
          message={toMessage(query.error)}
          onRetry={() => void query.refetch()}
        />
      ) : query.data.length === 0 ? (
        <EmptyState
          description="Crea al menos un barbero para poder recibir turnos."
          title="Sin barberos"
        />
      ) : (
        <ul className="divide-y divide-line">
          {query.data.map((barber) => (
            <li
              className="flex flex-wrap items-start justify-between gap-3 px-4 py-4 sm:px-5"
              key={barber.id}
            >
              <div className="min-w-0">
                <div className="flex flex-wrap items-center gap-2">
                  <p className="font-medium">{barber.display_name}</p>
                  {barber.is_active ? null : (
                    <Badge tone="neutral">Inactivo</Badge>
                  )}
                </div>
                <p className="mt-0.5 text-sm text-ink-muted">
                  {barber.email}
                  {barber.phone ? ` · ${barber.phone}` : ""}
                </p>
                {barber.bio ? (
                  <p className="mt-1 text-sm text-ink-muted">{barber.bio}</p>
                ) : null}
              </div>
              <Button
                isLoading={
                  toggle.isPending && toggle.variables?.id === barber.id
                }
                onClick={() =>
                  toggle.mutate({
                    id: barber.id,
                    is_active: !barber.is_active,
                  })
                }
                size="sm"
                variant="secondary"
              >
                {barber.is_active ? "Desactivar" : "Activar"}
              </Button>
            </li>
          ))}
        </ul>
      )}

      {toggle.isError ? (
        <div className="p-4 sm:p-5">
          <FormMessage tone="error">{toMessage(toggle.error)}</FormMessage>
        </div>
      ) : null}
    </Card>
  );
}
