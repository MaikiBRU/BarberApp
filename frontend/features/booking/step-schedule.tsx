"use client";

import { Button } from "@/components/ui/button";
import { InputField } from "@/components/ui/field";
import {
  EmptyState,
  ErrorState,
  SkeletonRows,
} from "@/components/ui/states";
import type { SlotChoice } from "@/features/booking/use-booking-state";
import { cn } from "@/lib/cn";
import { toMessage } from "@/lib/error-messages";
import { addDays, formatDateString, formatTime, shopToday } from "@/lib/format";

type StepScheduleProps = {
  date: string;
  onDateChange: (date: string) => void;
  slots: SlotChoice[];
  selectedSlot: SlotChoice | null;
  onSelectSlot: (slot: SlotChoice) => void;
  showBarberName: boolean;
  isLoading: boolean;
  isError: boolean;
  error: unknown;
  onRetry: () => void;
  isOpenDay: boolean;
};

export function StepSchedule({
  date,
  onDateChange,
  slots,
  selectedSlot,
  onSelectSlot,
  showBarberName,
  isLoading,
  isError,
  error,
  onRetry,
  isOpenDay,
}: StepScheduleProps) {
  const today = shopToday();

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-end gap-3">
        <InputField
          className="max-w-52"
          label="Fecha"
          min={today}
          onChange={(event) => onDateChange(event.target.value)}
          type="date"
          value={date}
        />
        <div className="flex gap-2 pb-0.5">
          <Button
            onClick={() => onDateChange(today)}
            size="sm"
            variant="secondary"
          >
            Hoy
          </Button>
          <Button
            onClick={() => onDateChange(addDays(today, 1))}
            size="sm"
            variant="secondary"
          >
            Manana
          </Button>
        </div>
      </div>

      <div>
        <h3 className="text-sm font-semibold">
          Horarios de {formatDateString(date)}
        </h3>

        {isLoading ? (
          <SkeletonRows rows={2} />
        ) : isError ? (
          <ErrorState
            message={toMessage(error)}
            onRetry={onRetry}
            title="No pudimos consultar la disponibilidad"
          />
        ) : !isOpenDay ? (
          <EmptyState
            description="Elegi otro dia para ver horarios disponibles."
            title="La barberia esta cerrada ese dia"
          />
        ) : slots.length === 0 ? (
          <EmptyState
            description="Probá con otra fecha o con otro barbero."
            title="No quedan horarios para esa fecha"
          />
        ) : (
          <ul className="mt-3 grid grid-cols-3 gap-2 sm:grid-cols-4 md:grid-cols-5">
            {slots.map((slot) => {
              const isSelected =
                selectedSlot?.startsAt === slot.startsAt &&
                selectedSlot?.barberUserId === slot.barberUserId;

              return (
                <li key={`${slot.startsAt}-${slot.barberUserId}`}>
                  <button
                    aria-pressed={isSelected}
                    className={cn(
                      "w-full rounded-md border px-2 py-2.5 text-sm font-medium transition-colors",
                      isSelected
                        ? "border-brand bg-brand text-on-brand"
                        : "border-line hover:border-line-strong",
                    )}
                    onClick={() => onSelectSlot(slot)}
                    type="button"
                  >
                    {formatTime(slot.startsAt)}
                    {showBarberName ? (
                      <span className="mt-0.5 block text-xs font-normal opacity-80">
                        {slot.barberName}
                      </span>
                    ) : null}
                  </button>
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </div>
  );
}
