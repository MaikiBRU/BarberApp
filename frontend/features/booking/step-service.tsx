"use client";

import {
  EmptyState,
  ErrorState,
  SkeletonRows,
} from "@/components/ui/states";
import { OptionRow } from "@/features/booking/option-list";
import type { QueryLike } from "@/features/booking/query-like";
import { toMessage } from "@/lib/error-messages";
import { formatDuration, formatPrice } from "@/lib/format";
import type { ProductExtraRead, ServiceRead } from "@/types/domain";

type StepServiceProps = {
  services: QueryLike<ServiceRead[]>;
  extras: QueryLike<ProductExtraRead[]>;
  selectedServiceId: string | null;
  selectedExtraIds: string[];
  onSelectService: (id: string) => void;
  onToggleExtra: (id: string) => void;
};

export function StepService({
  services,
  extras,
  selectedServiceId,
  selectedExtraIds,
  onSelectService,
  onToggleExtra,
}: StepServiceProps) {
  if (services.isPending) {
    return <SkeletonRows rows={3} />;
  }
  if (services.isError || !services.data) {
    return (
      <ErrorState
        message={toMessage(services.error)}
        onRetry={services.refetch}
      />
    );
  }
  if (services.data.length === 0) {
    return (
      <EmptyState
        description="La barbería todavía no publicó su carta de servicios."
        title="Sin servicios disponibles"
      />
    );
  }

  return (
    <div className="space-y-6">
      <fieldset className="space-y-2">
        <legend className="mb-2 text-sm font-semibold">
          Elegí un servicio
        </legend>
        {services.data.map((service) => (
          <OptionRow
            description={service.description}
            isSelected={selectedServiceId === service.id}
            key={service.id}
            meta={formatDuration(service.duration_minutes)}
            onSelect={() => onSelectService(service.id)}
            price={formatPrice(service.price_cents)}
            title={service.name}
          />
        ))}
      </fieldset>

      {extras.data && extras.data.length > 0 ? (
        <fieldset className="space-y-2">
          <legend className="mb-2 text-sm font-semibold">
            Extras (opcional)
          </legend>
          {extras.data.map((extra) => (
            <OptionRow
              description={extra.description}
              isSelected={selectedExtraIds.includes(extra.id)}
              key={extra.id}
              meta={
                extra.duration_minutes
                  ? `+${formatDuration(extra.duration_minutes)}`
                  : undefined
              }
              onSelect={() => onToggleExtra(extra.id)}
              price={formatPrice(extra.price_cents)}
              title={extra.name}
            />
          ))}
        </fieldset>
      ) : null}
    </div>
  );
}
