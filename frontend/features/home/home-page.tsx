"use client";

import { useQuery } from "@tanstack/react-query";

import { LinkButton } from "@/components/ui/button";
import { Card, CardHeader } from "@/components/ui/card";
import {
  EmptyState,
  ErrorState,
  SkeletonRows,
} from "@/components/ui/states";
import { PageContainer } from "@/components/layout/app-shell";
import { toMessage } from "@/lib/error-messages";
import { formatDuration, formatPrice } from "@/lib/format";
import { routes } from "@/lib/routes";
import { weekdayLabels } from "@/lib/status";
import { listServices } from "@/services/catalog";
import { listBusinessHours } from "@/services/schedule";

export function HomePage() {
  const services = useQuery({
    queryKey: ["services", "public"],
    queryFn: listServices,
  });
  const hours = useQuery({
    queryKey: ["business-hours"],
    queryFn: listBusinessHours,
  });

  return (
    <PageContainer>
      <section className="grid gap-8 lg:grid-cols-[1.05fr_0.95fr] lg:items-start">
        <div className="pt-2">
          <p className="text-xs font-semibold uppercase tracking-wide text-accent">
            Barberia
          </p>
          <h1 className="mt-3 text-4xl font-semibold leading-tight tracking-tight sm:text-5xl">
            Reserva tu turno sin mensajes de ida y vuelta.
          </h1>
          <p className="mt-4 max-w-xl text-base text-ink-muted">
            Elegi el servicio, el barbero y el horario. La disponibilidad se
            calcula en el momento, asi que lo que ves es lo que hay.
          </p>
          <div className="mt-6 flex flex-col gap-3 sm:flex-row">
            <LinkButton href={routes.booking}>Reservar turno</LinkButton>
            <LinkButton href={routes.appointments} variant="secondary">
              Ver mis turnos
            </LinkButton>
          </div>

          <div className="mt-10">
            <h2 className="text-sm font-semibold">Horarios de atencion</h2>
            {hours.isPending ? (
              <div className="mt-3 space-y-2">
                <SkeletonRows rows={2} />
              </div>
            ) : hours.isError ? (
              <p className="mt-3 text-sm text-ink-muted">
                No pudimos cargar los horarios en este momento.
              </p>
            ) : (
              <dl className="mt-3 max-w-sm divide-y divide-line border-y border-line text-sm">
                {hours.data.map((day) => (
                  <div
                    className="flex justify-between py-2"
                    key={day.weekday}
                  >
                    <dt className="text-ink-muted">
                      {weekdayLabels[day.weekday]}
                    </dt>
                    <dd className="font-medium">
                      {day.is_closed
                        ? "Cerrado"
                        : `${day.opens_at.slice(0, 5)} - ${day.closes_at.slice(0, 5)}`}
                    </dd>
                  </div>
                ))}
              </dl>
            )}
          </div>
        </div>

        <Card>
          <CardHeader
            description="Precios y duracion reales del catalogo."
            title="Servicios"
          />
          {services.isPending ? (
            <SkeletonRows rows={3} />
          ) : services.isError ? (
            <ErrorState
              message={toMessage(services.error)}
              onRetry={() => services.refetch()}
              isRetrying={services.isFetching}
            />
          ) : services.data.length === 0 ? (
            <EmptyState
              description="Todavia no hay servicios publicados."
              title="Sin servicios"
            />
          ) : (
            <ul className="divide-y divide-line">
              {services.data.map((service) => (
                <li
                  className="flex items-start justify-between gap-4 px-4 py-4 sm:px-5"
                  key={service.id}
                >
                  <div>
                    <p className="font-medium">{service.name}</p>
                    {service.description ? (
                      <p className="mt-0.5 text-sm text-ink-muted">
                        {service.description}
                      </p>
                    ) : null}
                    <p className="mt-1 text-sm text-ink-muted">
                      {formatDuration(service.duration_minutes)}
                    </p>
                  </div>
                  <p className="shrink-0 font-semibold">
                    {formatPrice(service.price_cents)}
                  </p>
                </li>
              ))}
            </ul>
          )}
        </Card>
      </section>
    </PageContainer>
  );
}
