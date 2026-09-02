import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { StatusActions } from "@/features/appointments/status-actions";
import {
  formatDateTime,
  formatDuration,
  formatPrice,
  formatTime,
} from "@/lib/format";
import { routes } from "@/lib/routes";
import { appointmentStatusMeta } from "@/lib/status";
import type { AppointmentRead } from "@/types/domain";

type AppointmentRowProps = {
  appointment: AppointmentRead;
  /** Show the customer instead of the barber (staff views). */
  perspective?: "customer" | "staff";
  /** Show only the time, for a single-day agenda. */
  compact?: boolean;
  showActions?: boolean;
};

export function AppointmentRow({
  appointment,
  perspective = "customer",
  compact = false,
  showActions = true,
}: AppointmentRowProps) {
  const status = appointmentStatusMeta[appointment.status];
  const isActive =
    appointment.status === "pending" || appointment.status === "confirmed";
  const counterpart =
    perspective === "staff" ? appointment.customer : appointment.barber;

  return (
    <article className="grid gap-3 px-4 py-4 sm:grid-cols-[auto_1fr_auto] sm:items-start sm:gap-5 sm:px-5">
      <p className="text-sm font-semibold sm:w-28">
        {compact
          ? formatTime(appointment.starts_at)
          : formatDateTime(appointment.starts_at)}
      </p>

      <div className="min-w-0">
        <div className="flex flex-wrap items-center gap-2">
          <Link
            className="font-medium underline-offset-4 hover:underline"
            href={routes.appointment(appointment.id)}
          >
            {appointment.service.name}
          </Link>
          <Badge tone={status.tone}>{status.label}</Badge>
        </div>
        <p className="mt-1 text-sm text-ink-muted">
          {perspective === "staff" ? "Cliente" : "Barbero"}:{" "}
          {counterpart.name}
          {counterpart.phone ? ` · ${counterpart.phone}` : ""}
        </p>
        <p className="mt-0.5 text-sm text-ink-muted">
          {formatDuration(appointment.duration_minutes)} ·{" "}
          {formatPrice(appointment.total_price_cents)}
          {appointment.extras.length
            ? ` · ${appointment.extras.map((extra) => extra.name).join(", ")}`
            : ""}
        </p>
        {appointment.notes ? (
          <p className="mt-1 text-sm italic text-ink-muted">
            &ldquo;{appointment.notes}&rdquo;
          </p>
        ) : null}
      </div>

      {showActions ? (
        <div className="sm:justify-self-end">
          {appointment.allowed_transitions.length > 0 ? (
            <StatusActions appointment={appointment} />
          ) : perspective === "customer" && isActive ? (
            <p className="text-xs text-ink-muted sm:max-w-40 sm:text-right">
              Ya no se puede cancelar online. Comunicate con la barbería.
            </p>
          ) : null}
        </div>
      ) : null}
    </article>
  );
}
