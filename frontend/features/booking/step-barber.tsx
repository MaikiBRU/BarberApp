"use client";

import {
  EmptyState,
  ErrorState,
  SkeletonRows,
} from "@/components/ui/states";
import { OptionRow } from "@/features/booking/option-list";
import type { QueryLike } from "@/features/booking/query-like";
import { toMessage } from "@/lib/error-messages";
import type { BarberRead } from "@/types/domain";

type StepBarberProps = {
  barbers: QueryLike<BarberRead[]>;
  selectedBarberId: string | null;
  onSelect: (id: string | null) => void;
};

export function StepBarber({
  barbers,
  selectedBarberId,
  onSelect,
}: StepBarberProps) {
  if (barbers.isPending) {
    return <SkeletonRows rows={2} />;
  }
  if (barbers.isError || !barbers.data) {
    return (
      <ErrorState
        message={toMessage(barbers.error)}
        onRetry={barbers.refetch}
      />
    );
  }
  if (barbers.data.length === 0) {
    return (
      <EmptyState
        description="No hay barberos disponibles para reservar en este momento."
        title="Sin barberos activos"
      />
    );
  }

  return (
    <fieldset className="space-y-2">
      <legend className="mb-2 text-sm font-semibold">
        Elegi con quien te atendes
      </legend>
      <OptionRow
        description="Te asignamos el primero disponible en el horario que elijas."
        isSelected={selectedBarberId === null}
        onSelect={() => onSelect(null)}
        title="Cualquier barbero"
      />
      {barbers.data.map((barber) => (
        <OptionRow
          description={barber.bio}
          isSelected={selectedBarberId === barber.id}
          key={barber.id}
          onSelect={() => onSelect(barber.id)}
          title={barber.display_name}
        />
      ))}
    </fieldset>
  );
}
