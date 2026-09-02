"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { LinkButton } from "@/components/ui/button";
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
import { routes } from "@/lib/routes";
import { listAppointments } from "@/services/appointments";
import type { AppointmentStatus } from "@/types/domain";

type Filter = {
  id: string;
  label: string;
  statuses?: AppointmentStatus[];
  upcomingOnly: boolean;
};

const filters: Filter[] = [
  {
    id: "upcoming",
    label: "Proximos",
    statuses: ["pending", "confirmed"],
    upcomingOnly: true,
  },
  { id: "history", label: "Historial", upcomingOnly: false },
];

export function MyAppointments() {
  const { token } = useSession();
  const [activeFilter, setActiveFilter] = useState<Filter>(filters[0]);

  const query = useQuery({
    queryKey: ["appointments", "mine", activeFilter.id],
    queryFn: () =>
      listAppointments(token as string, {
        statuses: activeFilter.statuses,
        dateFrom: activeFilter.upcomingOnly
          ? new Date().toISOString()
          : undefined,
        newestFirst: !activeFilter.upcomingOnly,
        limit: 50,
      }),
    enabled: Boolean(token),
  });

  return (
    <Card>
      <CardHeader
        action={
          <LinkButton href={routes.booking} size="sm">
            Reservar
          </LinkButton>
        }
        description="Consulta el estado de cada turno y cancela cuando lo necesites."
        title="Mis turnos"
      />

      <div
        className="flex gap-2 border-b border-line px-4 py-3 sm:px-5"
        role="tablist"
      >
        {filters.map((filter) => (
          <button
            aria-selected={activeFilter.id === filter.id}
            className={cn(
              "rounded-md px-3 py-1.5 text-sm font-medium transition-colors",
              activeFilter.id === filter.id
                ? "bg-surface-muted text-ink"
                : "text-ink-muted hover:text-ink",
            )}
            key={filter.id}
            onClick={() => setActiveFilter(filter)}
            role="tab"
            type="button"
          >
            {filter.label}
          </button>
        ))}
      </div>

      {query.isPending ? (
        <SkeletonRows rows={3} />
      ) : query.isError ? (
        <ErrorState
          message={toMessage(query.error)}
          onRetry={() => void query.refetch()}
        />
      ) : query.data.items.length === 0 ? (
        <EmptyState
          action={
            <LinkButton href={routes.booking}>Reservar un turno</LinkButton>
          }
          description={
            activeFilter.upcomingOnly
              ? "No tenes turnos proximos agendados."
              : "Todavia no tenes turnos en tu historial."
          }
          title="Sin turnos"
        />
      ) : (
        <div className="divide-y divide-line">
          {query.data.items.map((appointment) => (
            <AppointmentRow
              appointment={appointment}
              key={appointment.id}
              perspective="customer"
            />
          ))}
        </div>
      )}
    </Card>
  );
}
