import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { StepSchedule } from "@/features/booking/step-schedule";
import { ApiError } from "@/lib/api-client";
import type { SlotChoice } from "@/features/booking/use-booking-state";

const slots: SlotChoice[] = [
  {
    startsAt: "2026-09-10T13:00:00Z",
    barberUserId: "u-1",
    barberName: "Tomas",
  },
];

function renderStep(overrides: Partial<Parameters<typeof StepSchedule>[0]>) {
  const props = {
    date: "2026-09-10",
    onDateChange: vi.fn(),
    slots: [],
    selectedSlot: null,
    onSelectSlot: vi.fn(),
    showBarberName: false,
    isLoading: false,
    isError: false,
    error: null,
    onRetry: vi.fn(),
    isOpenDay: true,
    ...overrides,
  };
  render(<StepSchedule {...props} />);
  return props;
}

describe("StepSchedule", () => {
  it("shows a failure message, not an empty list, when the request fails", () => {
    renderStep({
      isError: true,
      error: new ApiError("El servidor no responde", 503, "http_error"),
    });

    expect(screen.getByRole("alert")).toHaveTextContent(
      "No pudimos consultar la disponibilidad",
    );
    expect(
      screen.queryByText("No quedan horarios para esa fecha"),
    ).not.toBeInTheDocument();
  });

  it("shows an empty state when the request succeeded with no slots", () => {
    renderStep({ slots: [] });

    expect(
      screen.getByText("No quedan horarios para esa fecha"),
    ).toBeInTheDocument();
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("explains a closed day instead of showing an empty grid", () => {
    renderStep({ isOpenDay: false });

    expect(
      screen.getByText("La barberia esta cerrada ese dia"),
    ).toBeInTheDocument();
  });

  it("renders one selectable button per available slot", async () => {
    const props = renderStep({ slots });

    const button = screen.getByRole("button", { name: /:/ });
    await userEvent.click(button);

    expect(props.onSelectSlot).toHaveBeenCalledWith(slots[0]);
  });

  it("names the barber when the customer did not choose one", () => {
    renderStep({ slots, showBarberName: true });

    expect(screen.getByText("Tomas")).toBeInTheDocument();
  });

  it("offers a retry action when the request failed", async () => {
    const props = renderStep({
      isError: true,
      error: new ApiError("Fallo", 500, "internal_error"),
    });

    await userEvent.click(screen.getByRole("button", { name: "Reintentar" }));

    expect(props.onRetry).toHaveBeenCalled();
  });
});
