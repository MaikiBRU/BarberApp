"use client";

import { useQuery } from "@tanstack/react-query";

import { Card, CardHeader } from "@/components/ui/card";
import {
  EmptyState,
  ErrorState,
  SkeletonRows,
} from "@/components/ui/states";
import { AppointmentRow } from "@/features/appointments/appointment-row";
import {
  MetricGrid,
  MetricGridSkeleton,
} from "@/features/dashboard/metric-grid";
import { useSession } from "@/hooks/use-session";
import { toMessage } from "@/lib/error-messages";
import { formatDateString, formatPrice } from "@/lib/format";
import { fetchDashboardSummary, fetchTodayAgenda } from "@/services/dashboard";

export function DashboardOverview() {
  const { token, isAdmin } = useSession();

  const summary = useQuery({
    queryKey: ["dashboard", "summary"],
    queryFn: () => fetchDashboardSummary(token as string),
    enabled: Boolean(token),
  });
  const agenda = useQuery({
    queryKey: ["dashboard", "today"],
    queryFn: () => fetchTodayAgenda(token as string),
    enabled: Boolean(token),
  });

  return (
    <div className="space-y-5">
      {summary.isPending ? (
        <MetricGridSkeleton />
      ) : summary.isError ? (
        <Card>
          <ErrorState
            message={toMessage(summary.error)}
            onRetry={() => void summary.refetch()}
            title="No pudimos cargar las metricas"
          />
        </Card>
      ) : (
        <MetricGrid
          metrics={[
            {
              label: "Turnos hoy",
              value: String(
                summary.data.today.pending +
                  summary.data.today.confirmed +
                  summary.data.today.completed,
              ),
              hint: `${summary.data.today.pending} pendientes de confirmar`,
            },
            {
              label: "Próximos turnos",
              value: String(summary.data.upcoming_count),
              hint: "Activos después de hoy",
            },
            {
              label: "Facturado hoy",
              value: formatPrice(summary.data.today_revenue_cents),
              hint: "Solo turnos completados",
            },
            isAdmin
              ? {
                  label: "Facturado en el mes",
                  value: formatPrice(summary.data.month_revenue_cents),
                  hint: `${summary.data.active_barbers} barberos activos`,
                }
              : {
                  label: "Completados hoy",
                  value: String(summary.data.today.completed),
                  hint: `${summary.data.today.no_show} ausencias`,
                },
          ]}
        />
      )}

      <Card>
        <CardHeader
          description={
            summary.data
              ? formatDateString(summary.data.date)
              : "Turnos de la jornada"
          }
          title="Agenda de hoy"
        />
        {agenda.isPending ? (
          <SkeletonRows rows={3} />
        ) : agenda.isError ? (
          <ErrorState
            message={toMessage(agenda.error)}
            onRetry={() => void agenda.refetch()}
          />
        ) : agenda.data.length === 0 ? (
          <EmptyState
            description="No hay turnos agendados para hoy."
            title="Día libre"
          />
        ) : (
          <div className="divide-y divide-line">
            {agenda.data.map((appointment) => (
              <AppointmentRow
                appointment={appointment}
                compact
                key={appointment.id}
                perspective="staff"
              />
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}
