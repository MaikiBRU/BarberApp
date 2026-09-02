"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardHeader } from "@/components/ui/card";
import {
  ErrorState,
  FormMessage,
  SkeletonRows,
} from "@/components/ui/states";
import { useSession } from "@/hooks/use-session";
import { toMessage } from "@/lib/error-messages";
import { weekdayLabels } from "@/lib/status";
import {
  listBusinessHours,
  replaceBusinessHours,
} from "@/services/schedule";
import type { BusinessHours } from "@/types/domain";

function toTimeInput(value: string): string {
  return value.slice(0, 5);
}

export function HoursManager() {
  const { token } = useSession();
  const queryClient = useQueryClient();
  // `draft` stays null until the admin edits a row, so the table renders
  // straight from server data instead of mirroring it in an effect.
  const [draft, setDraft] = useState<BusinessHours[] | null>(null);
  const [isSaved, setSaved] = useState(false);

  const query = useQuery({
    queryKey: ["business-hours"],
    queryFn: listBusinessHours,
  });

  const days = draft ?? query.data ?? [];

  const save = useMutation({
    mutationFn: () =>
      replaceBusinessHours(
        token as string,
        days.map((day) => ({
          ...day,
          opens_at: `${toTimeInput(day.opens_at)}:00`,
          closes_at: `${toTimeInput(day.closes_at)}:00`,
        })),
      ),
    onSuccess: (updated) => {
      queryClient.setQueryData(["business-hours"], updated);
      void queryClient.invalidateQueries({ queryKey: ["availability"] });
      setDraft(null);
      setSaved(true);
    },
  });

  function updateDay(weekday: number, patch: Partial<BusinessHours>) {
    setSaved(false);
    setDraft(
      days.map((day) =>
        day.weekday === weekday ? { ...day, ...patch } : day,
      ),
    );
  }

  return (
    <Card>
      <CardHeader
        description="Definen que horarios se ofrecen al reservar."
        title="Horarios de atención"
      />

      {query.isPending ? (
        <SkeletonRows rows={4} />
      ) : query.isError ? (
        <ErrorState
          message={toMessage(query.error)}
          onRetry={() => void query.refetch()}
        />
      ) : (
        <div className="p-4 sm:p-5">
          <ul className="divide-y divide-line">
            {days.map((day) => (
              <li
                className="grid gap-3 py-3 sm:grid-cols-[1fr_auto_auto_auto] sm:items-center"
                key={day.weekday}
              >
                <p className="font-medium">{weekdayLabels[day.weekday]}</p>

                <label className="flex items-center gap-2 text-sm">
                  <span className="text-ink-muted">Abre</span>
                  <input
                    className="rounded-md border border-line-strong bg-surface px-2 py-1.5 disabled:opacity-50"
                    disabled={day.is_closed}
                    onChange={(event) =>
                      updateDay(day.weekday, {
                        opens_at: event.target.value,
                      })
                    }
                    type="time"
                    value={toTimeInput(day.opens_at)}
                  />
                </label>

                <label className="flex items-center gap-2 text-sm">
                  <span className="text-ink-muted">Cierra</span>
                  <input
                    className="rounded-md border border-line-strong bg-surface px-2 py-1.5 disabled:opacity-50"
                    disabled={day.is_closed}
                    onChange={(event) =>
                      updateDay(day.weekday, {
                        closes_at: event.target.value,
                      })
                    }
                    type="time"
                    value={toTimeInput(day.closes_at)}
                  />
                </label>

                <label className="flex items-center gap-2 text-sm">
                  <input
                    checked={day.is_closed}
                    onChange={(event) =>
                      updateDay(day.weekday, {
                        is_closed: event.target.checked,
                      })
                    }
                    type="checkbox"
                  />
                  <span>Cerrado</span>
                </label>
              </li>
            ))}
          </ul>

          <div className="mt-4 space-y-3">
            {save.isError ? (
              <FormMessage tone="error">{toMessage(save.error)}</FormMessage>
            ) : null}
            {isSaved && !save.isPending ? (
              <FormMessage tone="success">
                Horarios actualizados.
              </FormMessage>
            ) : null}
            <Button isLoading={save.isPending} onClick={() => save.mutate()}>
              Guardar horarios
            </Button>
          </div>
        </div>
      )}
    </Card>
  );
}
