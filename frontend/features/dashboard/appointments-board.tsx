"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardHeader } from "@/components/ui/card";
import {
  EmptyState,
  ErrorState,
  SkeletonRows,
} from "@/components/ui/states";
import { AppointmentRow } from "@/features/appointments/appointment-row";
import { useSession } from "@/hooks/use-session";
import { cn } from "@/lib/cn";
import { toMessage } from "@/lib/error-messages";
import { appointmentStatusMeta } from "@/lib/status";
import { listAppointments } from "@/services/appointments";
import type { AppointmentStatus } from "@/types/domain";

const PAGE_SIZE = 20;

const statusOptions: Array<{
  id: string;
  label: string;
  statuses?: AppointmentStatus[];
}> = [
  { id: "all", label: "Todos" },
  { id: "pending", label: appointmentStatusMeta.pending.label, statuses: ["pending"] },
  {
    id: "confirmed",
    label: appointmentStatusMeta.confirmed.label,
    statuses: ["confirmed"],
  },
  {
    id: "completed",
    label: appointmentStatusMeta.completed.label,
    statuses: ["completed"],
  },
  {
    id: "cancelled",
    label: appointmentStatusMeta.cancelled.label,
    statuses: ["cancelled", "no_show"],
  },
];

export function AppointmentsBoard() {
  const { token } = useSession();
  const [filterId, setFilterId] = useState("all");
  const [page, setPage] = useState(0);

  const filter = statusOptions.find((option) => option.id === filterId);

  const query = useQuery({
    queryKey: ["appointments", "board", filterId, page],
    queryFn: () =>
      listAppointments(token as string, {
        statuses: filter?.statuses,
        limit: PAGE_SIZE,
        offset: page * PAGE_SIZE,
        newestFirst: true,
      }),
    enabled: Boolean(token),
  });

  const total = query.data?.total ?? 0;
  const lastPage = Math.max(Math.ceil(total / PAGE_SIZE) - 1, 0);

  return (
    <Card>
      <CardHeader
        description="Filtrá por estado y cambia el estado de cada turno."
        title="Todos los turnos"
      />

      <div className="flex flex-wrap gap-2 border-b border-line px-4 py-3 sm:px-5">
        {statusOptions.map((option) => (
          <button
            aria-pressed={filterId === option.id}
            className={cn(
              "rounded-md px-3 py-1.5 text-sm font-medium transition-colors",
              filterId === option.id
                ? "bg-surface-muted text-ink"
                : "text-ink-muted hover:text-ink",
            )}
            key={option.id}
            onClick={() => {
              setFilterId(option.id);
              setPage(0);
            }}
            type="button"
          >
            {option.label}
          </button>
        ))}
      </div>

      {query.isPending ? (
        <SkeletonRows rows={4} />
      ) : query.isError ? (
        <ErrorState
          message={toMessage(query.error)}
          onRetry={() => void query.refetch()}
        />
      ) : query.data.items.length === 0 ? (
        <EmptyState
          description="No hay turnos que coincidan con este filtro."
          title="Sin resultados"
        />
      ) : (
        <>
          <div className="divide-y divide-line">
            {query.data.items.map((appointment) => (
              <AppointmentRow
                appointment={appointment}
                key={appointment.id}
                perspective="staff"
              />
            ))}
          </div>
          <div className="flex items-center justify-between gap-3 border-t border-line px-4 py-3 sm:px-5">
            <p className="text-sm text-ink-muted">
              {page * PAGE_SIZE + 1}-
              {page * PAGE_SIZE + query.data.items.length} de {total}
            </p>
            <div className="flex gap-2">
              <Button
                disabled={page === 0}
                onClick={() => setPage((current) => Math.max(current - 1, 0))}
                size="sm"
                variant="secondary"
              >
                Anterior
              </Button>
              <Button
                disabled={page >= lastPage}
                onClick={() =>
                  setPage((current) => Math.min(current + 1, lastPage))
                }
                size="sm"
                variant="secondary"
              >
                Siguiente
              </Button>
            </div>
          </div>
        </>
      )}
    </Card>
  );
}
