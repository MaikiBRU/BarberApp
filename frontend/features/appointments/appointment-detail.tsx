"use client";

import { useQuery } from "@tanstack/react-query";

import { Badge } from "@/components/ui/badge";
import { LinkButton } from "@/components/ui/button";
import { Card, CardHeader } from "@/components/ui/card";
import { ErrorState, SkeletonRows } from "@/components/ui/states";
import { StatusActions } from "@/features/appointments/status-actions";
import { useSession } from "@/hooks/use-session";
import { toMessage } from "@/lib/error-messages";
import {
  formatDateTime,
  formatDuration,
  formatPrice,
  formatTime,
} from "@/lib/format";
import { routes } from "@/lib/routes";
import {
  appointmentStatusMeta,
  paymentMethodLabels,
  paymentStatusMeta,
} from "@/lib/status";
import { fetchAppointment } from "@/services/appointments";

export function AppointmentDetail({ appointmentId }: { appointmentId: string }) {
  const { token } = useSession();
  const query = useQuery({
    queryKey: ["appointment", appointmentId],
    queryFn: () => fetchAppointment(token as string, appointmentId),
    enabled: Boolean(token),
  });

  if (query.isPending) {
    return (
      <Card>
        <SkeletonRows rows={4} />
      </Card>
    );
  }

  if (query.isError) {
    const isMissing =
      typeof query.error === "object" &&
      query.error !== null &&
      "status" in query.error &&
      (query.error as { status: number }).status === 404;

    return (
      <Card className="p-5">
        <ErrorState
          message={
            isMissing
              ? "Este turno no existe o no tenés permiso para verlo."
              : toMessage(query.error)
          }
          onRetry={isMissing ? undefined : () => void query.refetch()}
          title={isMissing ? "Turno no disponible" : undefined}
        />
        <LinkButton href={routes.appointments} variant="secondary">
          Volver a mis turnos
        </LinkButton>
      </Card>
    );
  }

  const appointment = query.data;
  const status = appointmentStatusMeta[appointment.status];
  const payment = paymentStatusMeta[appointment.payment_status];

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader
          action={<Badge tone={status.tone}>{status.label}</Badge>}
          description={`${formatDateTime(appointment.starts_at)} - ${formatTime(appointment.ends_at)}`}
          title={appointment.service.name}
        />
        <dl className="divide-y divide-line text-sm">
          <DetailRow label="Barbero" value={appointment.barber.name} />
          <DetailRow label="Cliente" value={appointment.customer.name} />
          {appointment.customer.phone ? (
            <DetailRow
              label="Teléfono del cliente"
              value={appointment.customer.phone}
            />
          ) : null}
          <DetailRow
            label="Duración"
            value={formatDuration(appointment.duration_minutes)}
          />
          <DetailRow
            label="Extras"
            value={
              appointment.extras.length
                ? appointment.extras
                    .map((extra) => extra.name)
                    .join(", ")
                : "Sin extras"
            }
          />
          <DetailRow
            label="Servicio"
            value={formatPrice(appointment.service_price_cents)}
          />
          {appointment.extras_price_cents > 0 ? (
            <DetailRow
              label="Extras"
              value={formatPrice(appointment.extras_price_cents)}
            />
          ) : null}
          <DetailRow
            label="Total"
            value={formatPrice(appointment.total_price_cents)}
          />
          <DetailRow
            label="Pago"
            value={`${
              appointment.payment_method
                ? paymentMethodLabels[appointment.payment_method]
                : "Sin definir"
            } - ${payment.label}`}
          />
          {appointment.notes ? (
            <DetailRow label="Notas" value={appointment.notes} />
          ) : null}
          {appointment.cancellation_reason ? (
            <DetailRow
              label="Motivo de cancelación"
              value={appointment.cancellation_reason}
            />
          ) : null}
        </dl>
      </Card>

      {appointment.allowed_transitions.length > 0 ? (
        <Card className="p-4 sm:p-5">
          <h2 className="text-sm font-semibold">Acciones disponibles</h2>
          <p className="mt-1 text-sm text-ink-muted">
            {appointment.can_cancel
              ? "Podés cancelar este turno desde acá."
              : "Estas son las acciones que tu cuenta puede realizar."}
          </p>
          <div className="mt-3">
            <StatusActions appointment={appointment} size="md" />
          </div>
        </Card>
      ) : null}
    </div>
  );
}

function DetailRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-wrap items-start justify-between gap-4 px-4 py-3 sm:px-5">
      <dt className="text-ink-muted">{label}</dt>
      <dd className="text-right font-medium">{value}</dd>
    </div>
  );
}
