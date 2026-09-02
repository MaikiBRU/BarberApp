"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import type { FormEvent } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardHeader } from "@/components/ui/card";
import { InputField } from "@/components/ui/field";
import {
  ErrorState,
  FormMessage,
  SkeletonRows,
} from "@/components/ui/states";
import { useSession } from "@/hooks/use-session";
import { toFieldErrors, toMessage } from "@/lib/error-messages";
import { fetchMyProfile, updateMyProfile } from "@/services/users";

export function ProfileForm() {
  const { token, user } = useSession();
  const queryClient = useQueryClient();
  // `draft` stays null until the person edits something, so the form
  // renders straight from server data without mirroring it in an effect.
  const [draft, setDraft] = useState<{
    fullName: string;
    phone: string;
  } | null>(null);
  const [isSaved, setSaved] = useState(false);

  const query = useQuery({
    queryKey: ["profile", "me"],
    queryFn: () => fetchMyProfile(token as string),
    enabled: Boolean(token),
  });

  const values = draft ?? {
    fullName: query.data?.full_name ?? "",
    phone: query.data?.phone ?? "",
  };
  const { fullName, phone } = values;

  const mutation = useMutation({
    mutationFn: () =>
      updateMyProfile(token as string, {
        full_name: fullName.trim() || null,
        phone: phone.trim() || null,
      }),
    onSuccess: (updated) => {
      queryClient.setQueryData(["profile", "me"], updated);
      setDraft(null);
      setSaved(true);
    },
  });

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaved(false);
    mutation.mutate();
  }

  const fieldErrors = toFieldErrors(mutation.error);

  return (
    <Card>
      <CardHeader
        description="Estos datos ayudan al barbero a contactarte si hay un cambio."
        title="Mis datos"
      />

      {query.isPending ? (
        <SkeletonRows rows={2} />
      ) : query.isError ? (
        <ErrorState
          message={toMessage(query.error)}
          onRetry={() => void query.refetch()}
        />
      ) : (
        <form className="space-y-4 p-4 sm:p-5" noValidate onSubmit={handleSubmit}>
          <InputField
            disabled
            hint="El email no se puede cambiar desde aca."
            label="Email"
            readOnly
            value={query.data.email ?? user?.email ?? ""}
          />
          <InputField
            autoComplete="name"
            error={fieldErrors.full_name}
            label="Nombre y apellido"
            maxLength={120}
            onChange={(event) =>
              setDraft({ ...values, fullName: event.target.value })
            }
            value={fullName}
          />
          <InputField
            autoComplete="tel"
            error={fieldErrors.phone}
            label="Telefono"
            maxLength={40}
            onChange={(event) =>
              setDraft({ ...values, phone: event.target.value })
            }
            type="tel"
            value={phone}
          />

          {mutation.isError ? (
            <FormMessage tone="error">{toMessage(mutation.error)}</FormMessage>
          ) : null}
          {isSaved && !mutation.isPending ? (
            <FormMessage tone="success">Datos actualizados.</FormMessage>
          ) : null}

          <Button isLoading={mutation.isPending} type="submit">
            Guardar cambios
          </Button>
        </form>
      )}
    </Card>
  );
}
