import { describe, expect, it } from "vitest";

import {
  maxReachableStep,
  summarize,
  toSlotChoices,
} from "@/features/booking/use-booking-state";
import type {
  AvailabilityResponse,
  ProductExtraRead,
  ServiceRead,
} from "@/types/domain";

const service: ServiceRead = {
  id: "svc-1",
  shop_id: null,
  name: "Corte clásico",
  description: null,
  duration_minutes: 45,
  price_cents: 1300000,
  is_active: true,
  created_at: "2026-01-01T00:00:00Z",
};

const extra: ProductExtraRead = {
  id: "ext-1",
  shop_id: null,
  name: "Lavado",
  description: null,
  price_cents: 300000,
  duration_minutes: 15,
  is_active: true,
  created_at: "2026-01-01T00:00:00Z",
};

const availability: AvailabilityResponse = {
  date: "2026-09-10",
  service_id: "svc-1",
  duration_minutes: 45,
  slot_minutes: 15,
  is_open: true,
  barbers: [
    {
      barber_id: "b-1",
      barber_user_id: "u-1",
      display_name: "Tomas",
      slots: [
        { starts_at: "2026-09-10T13:00:00Z", ends_at: "2026-09-10T13:45:00Z" },
        { starts_at: "2026-09-10T14:00:00Z", ends_at: "2026-09-10T14:45:00Z" },
      ],
    },
    {
      barber_id: "b-2",
      barber_user_id: "u-2",
      display_name: "Lucia",
      slots: [
        { starts_at: "2026-09-10T12:00:00Z", ends_at: "2026-09-10T12:45:00Z" },
        { starts_at: "2026-09-10T13:00:00Z", ends_at: "2026-09-10T13:45:00Z" },
      ],
    },
  ],
};

describe("toSlotChoices", () => {
  it("returns one entry per start time, ordered chronologically", () => {
    const slots = toSlotChoices(availability);

    expect(slots.map((slot) => slot.startsAt)).toEqual([
      "2026-09-10T12:00:00Z",
      "2026-09-10T13:00:00Z",
      "2026-09-10T14:00:00Z",
    ]);
  });

  it("keeps the first barber free at each start time", () => {
    const slots = toSlotChoices(availability);

    expect(slots[0].barberName).toBe("Lucia");
    expect(slots[1].barberName).toBe("Tomas");
  });

  it("returns nothing when availability has not loaded", () => {
    expect(toSlotChoices(undefined)).toEqual([]);
  });
});

describe("summarize", () => {
  it("adds the duration and price of every selected extra", () => {
    const result = summarize(service, [extra], ["ext-1"]);

    expect(result.totalMinutes).toBe(60);
    expect(result.totalCents).toBe(1600000);
    expect(result.chosenExtras).toHaveLength(1);
  });

  it("ignores extras that are not selected", () => {
    const result = summarize(service, [extra], []);

    expect(result.totalMinutes).toBe(45);
    expect(result.totalCents).toBe(1300000);
  });

  it("returns zeroes before a service is chosen", () => {
    const result = summarize(undefined, [extra], []);

    expect(result.totalMinutes).toBe(0);
    expect(result.totalCents).toBe(0);
  });
});

describe("maxReachableStep", () => {
  const base = {
    step: 0,
    serviceId: null,
    extraIds: [],
    barberId: null,
    date: "2026-09-10",
    slot: null,
  };

  it("keeps the customer on the first step until a service is chosen", () => {
    expect(maxReachableStep(base)).toBe(0);
  });

  it("allows reaching the schedule step once a service is chosen", () => {
    expect(maxReachableStep({ ...base, serviceId: "svc-1" })).toBe(2);
  });

  it("unlocks confirmation only after a slot is selected", () => {
    expect(
      maxReachableStep({
        ...base,
        serviceId: "svc-1",
        slot: {
          startsAt: "2026-09-10T13:00:00Z",
          barberUserId: "u-1",
          barberName: "Tomas",
        },
      }),
    ).toBe(3);
  });
});
