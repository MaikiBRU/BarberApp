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
import { formatDuration, formatPrice, toCents } from "@/lib/format";
import { createExtra, listAllExtras, updateExtra } from "@/services/catalog";

export function ExtraManager() {
  const { token } = useSession();
  const queryClient = useQueryClient();
  const [isFormOpen, setFormOpen] = useState(false);

  const query = useQuery({
    queryKey: ["extras", "admin"],
    queryFn: () => listAllExtras(token as string),
    enabled: Boolean(token),
  });

  function invalidate() {
    void queryClient.invalidateQueries({ queryKey: ["extras"] });
    void queryClient.invalidateQueries({ queryKey: ["availability"] });
  }

  const create = useMutation({
    mutationFn: (input: {
      name: string;
      description: string | null;
      duration_minutes: number;
      price_cents: number;
    }) => createExtra(token as string, input),
    onSuccess: () => {
      invalidate();
      setFormOpen(false);
    },
  });

  const toggle = useMutation({
    mutationFn: (input: { id: string; is_active: boolean }) =>
      updateExtra(token as string, input.id, { is_active: input.is_active }),
    onSuccess: invalidate,
  });

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    create.mutate({
      name: String(data.get("name") ?? ""),
      description: String(data.get("description") ?? "") || null,
      duration_minutes: Number(data.get("duration") ?? 0),
      price_cents: toCents(String(data.get("price") ?? "0")),
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
            {isFormOpen ? "Cancelar" : "Nuevo extra"}
          </Button>
        }
        description="Los extras suman tiempo y precio al turno."
        title="Extras"
      />

      {isFormOpen ? (
        <form
          className="grid gap-4 border-b border-line p-4 sm:grid-cols-2 sm:p-5"
          noValidate
          onSubmit={handleSubmit}
        >
          <InputField
            error={fieldErrors.name}
            label="Nombre"
            maxLength={120}
            name="name"
            required
          />
          <InputField
            error={fieldErrors.duration_minutes}
            hint="0 si no agrega tiempo al turno."
            label="Duración extra (minutos)"
            max={240}
            min={0}
            name="duration"
            required
            type="number"
          />
          <InputField
            error={fieldErrors.price_cents}
            label="Precio"
            min={0}
            name="price"
            required
            step="0.01"
            type="number"
          />
          <div className="sm:col-span-2">
            <TextareaField
              error={fieldErrors.description}
              label="Descripción"
              maxLength={1000}
              name="description"
            />
          </div>
          {create.isError ? (
            <div className="sm:col-span-2">
              <FormMessage tone="error">{toMessage(create.error)}</FormMessage>
            </div>
          ) : null}
          <div className="sm:col-span-2">
            <Button isLoading={create.isPending} type="submit">
              Crear extra
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
          description="Los extras son opcionales; podés crearlos cuando quieras."
          title="Sin extras"
        />
      ) : (
        <ul className="divide-y divide-line">
          {query.data.map((extra) => (
            <li
              className="flex flex-wrap items-start justify-between gap-3 px-4 py-4 sm:px-5"
              key={extra.id}
            >
              <div className="min-w-0">
                <div className="flex flex-wrap items-center gap-2">
                  <p className="font-medium">{extra.name}</p>
                  {extra.is_active ? null : (
                    <Badge tone="neutral">Inactivo</Badge>
                  )}
                </div>
                {extra.description ? (
                  <p className="mt-0.5 text-sm text-ink-muted">
                    {extra.description}
                  </p>
                ) : null}
                <p className="mt-1 text-sm text-ink-muted">
                  {extra.duration_minutes
                    ? `+${formatDuration(extra.duration_minutes)} · `
                    : ""}
                  {formatPrice(extra.price_cents)}
                </p>
              </div>
              <Button
                isLoading={
                  toggle.isPending && toggle.variables?.id === extra.id
                }
                onClick={() =>
                  toggle.mutate({
                    id: extra.id,
                    is_active: !extra.is_active,
                  })
                }
                size="sm"
                variant="secondary"
              >
                {extra.is_active ? "Desactivar" : "Activar"}
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
