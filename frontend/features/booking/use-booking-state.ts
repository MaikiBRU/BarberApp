"use client";

import { useMemo, useState } from "react";

import { shopToday } from "@/lib/format";
import type {
  AvailabilityResponse,
  ProductExtraRead,
  ServiceRead,
} from "@/types/domain";

export type SlotChoice = {
  startsAt: string;
  barberUserId: string;
  barberName: string;
};

export type BookingState = {
  step: number;
  serviceId: string | null;
  extraIds: string[];
  barberId: string | null;
  date: string;
  slot: SlotChoice | null;
};

const initialState: BookingState = {
  step: 0,
  serviceId: null,
  extraIds: [],
  barberId: null,
  date: shopToday(),
  slot: null,
};

export function useBookingState() {
  const [state, setState] = useState<BookingState>(initialState);

  const actions = useMemo(
    () => ({
      goTo: (step: number) =>
        setState((prev) => ({ ...prev, step })),

      // Changing the service invalidates the chosen slot: its duration
      // decides which start times are still valid.
      selectService: (serviceId: string) =>
        setState((prev) => ({
          ...prev,
          serviceId,
          slot: prev.serviceId === serviceId ? prev.slot : null,
        })),

      toggleExtra: (extraId: string) =>
        setState((prev) => ({
          ...prev,
          slot: null,
          extraIds: prev.extraIds.includes(extraId)
            ? prev.extraIds.filter((id) => id !== extraId)
            : [...prev.extraIds, extraId],
        })),

      selectBarber: (barberId: string | null) =>
        setState((prev) => ({ ...prev, barberId, slot: null })),

      selectDate: (date: string) =>
        setState((prev) => ({ ...prev, date, slot: null })),

      selectSlot: (slot: SlotChoice | null) =>
        setState((prev) => ({ ...prev, slot })),

      reset: () => setState({ ...initialState, date: shopToday() }),
    }),
    [],
  );

  return { state, actions };
}

/** Highest step the customer may jump to given the current choices. */
export function maxReachableStep(state: BookingState): number {
  if (!state.serviceId) {
    return 0;
  }
  if (!state.slot) {
    return 2;
  }
  return 3;
}

/** Flatten availability into one ordered list of selectable slots. */
export function toSlotChoices(
  availability: AvailabilityResponse | undefined,
): SlotChoice[] {
  if (!availability) {
    return [];
  }

  const byStart = new Map<string, SlotChoice>();
  for (const barber of availability.barbers) {
    for (const slot of barber.slots) {
      if (!byStart.has(slot.starts_at)) {
        byStart.set(slot.starts_at, {
          startsAt: slot.starts_at,
          barberUserId: barber.barber_user_id,
          barberName: barber.display_name,
        });
      }
    }
  }

  return [...byStart.values()].sort((left, right) =>
    left.startsAt.localeCompare(right.startsAt),
  );
}

/** Total price and duration for the current selection. */
export function summarize(
  service: ServiceRead | undefined,
  extras: ProductExtraRead[],
  selectedExtraIds: string[],
) {
  const chosen = extras.filter((extra) =>
    selectedExtraIds.includes(extra.id),
  );
  return {
    chosenExtras: chosen,
    totalCents:
      (service?.price_cents ?? 0) +
      chosen.reduce((sum, extra) => sum + extra.price_cents, 0),
    totalMinutes:
      (service?.duration_minutes ?? 0) +
      chosen.reduce((sum, extra) => sum + extra.duration_minutes, 0),
  };
}
