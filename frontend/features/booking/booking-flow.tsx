"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { BookingFooter } from "@/features/booking/booking-footer";
import { StepBarber } from "@/features/booking/step-barber";
import { StepConfirm } from "@/features/booking/step-confirm";
import { StepSchedule } from "@/features/booking/step-schedule";
import { Stepper, bookingSteps } from "@/features/booking/stepper";
import {
  maxReachableStep,
  summarize,
  toSlotChoices,
  useBookingState,
} from "@/features/booking/use-booking-state";
import { StepService } from "@/features/booking/step-service";
import { useSession } from "@/hooks/use-session";
import { toMessage } from "@/lib/error-messages";
import { routes } from "@/lib/routes";
import {
  createAppointment,
  fetchAvailability,
} from "@/services/appointments";
import { listBarbers, listExtras, listServices } from "@/services/catalog";
import type { PaymentMethod } from "@/types/domain";

export function BookingFlow() {
  const { token, isReady, isAuthenticated } = useSession();
  const { state, actions } = useBookingState();
  const [paymentMethod, setPaymentMethod] = useState<PaymentMethod>("cash");
  const [notes, setNotes] = useState("");
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [confirmedId, setConfirmedId] = useState<string | null>(null);
  const [isSubmitting, setSubmitting] = useState(false);

  const services = useQuery({
    queryKey: ["services", "public"],
    queryFn: listServices,
  });
  const extras = useQuery({
    queryKey: ["extras", "public"],
    queryFn: listExtras,
  });
  const barbers = useQuery({
    queryKey: ["barbers", "public"],
    queryFn: listBarbers,
  });
  const availability = useQuery({
    queryKey: [
      "availability",
      state.serviceId,
      state.barberId,
      state.date,
      state.extraIds,
    ],
    queryFn: () =>
      fetchAvailability({
        serviceId: state.serviceId as string,
        date: state.date,
        barberId: state.barberId ?? undefined,
        extraIds: state.extraIds,
      }),
    enabled: Boolean(state.serviceId) && state.step >= 2,
  });

  const selectedService = services.data?.find(
    (service) => service.id === state.serviceId,
  );
  const { chosenExtras, totalCents, totalMinutes } = summarize(
    selectedService,
    extras.data ?? [],
    state.extraIds,
  );
  const slots = toSlotChoices(availability.data);

  async function handleConfirm() {
    if (!token || !state.slot || !state.serviceId) {
      return;
    }

    setSubmitting(true);
    setSubmitError(null);
    try {
      const created = await createAppointment(token, {
        barber_id: state.slot.barberUserId,
        service_id: state.serviceId,
        starts_at: state.slot.startsAt,
        extra_ids: state.extraIds,
        payment_method: paymentMethod,
        notes: notes.trim() || undefined,
      });
      setConfirmedId(created.id);
    } catch (error) {
      setSubmitError(toMessage(error));
      // The slot may have been taken while the customer was deciding,
      // so send them back to a freshly loaded grid.
      actions.selectSlot(null);
      actions.goTo(2);
      void availability.refetch();
    } finally {
      setSubmitting(false);
    }
  }

  if (confirmedId) {
    return (
      <Card className="p-5 sm:p-6">
        <h2 className="text-xl font-semibold">Turno reservado</h2>
        <p className="mt-2 text-sm text-ink-muted">
          Queda pendiente de confirmacion por la barberia.
        </p>
        <div className="mt-5 flex flex-col gap-2 sm:flex-row">
          <Link href={routes.appointment(confirmedId)}>
            <Button className="w-full sm:w-auto">Ver el turno</Button>
          </Link>
          <Button
            onClick={() => {
              setConfirmedId(null);
              setNotes("");
              actions.reset();
            }}
            variant="secondary"
          >
            Reservar otro
          </Button>
        </div>
      </Card>
    );
  }

  return (
    <Card>
      <div className="border-b border-line px-4 py-4 sm:px-5">
        <Stepper
          activeStep={state.step}
          maxReachable={maxReachableStep(state)}
          onSelect={actions.goTo}
        />
      </div>

      <div className="px-4 py-5 sm:px-5">
        {state.step === 0 ? (
          <StepService
            extras={extras}
            onSelectService={actions.selectService}
            onToggleExtra={actions.toggleExtra}
            selectedExtraIds={state.extraIds}
            selectedServiceId={state.serviceId}
            services={services}
          />
        ) : null}

        {state.step === 1 ? (
          <StepBarber
            barbers={barbers}
            onSelect={actions.selectBarber}
            selectedBarberId={state.barberId}
          />
        ) : null}

        {state.step === 2 ? (
          <StepSchedule
            date={state.date}
            error={availability.error}
            isError={availability.isError}
            isLoading={availability.isPending || availability.isFetching}
            isOpenDay={availability.data?.is_open ?? true}
            onDateChange={actions.selectDate}
            onRetry={() => void availability.refetch()}
            onSelectSlot={actions.selectSlot}
            selectedSlot={state.slot}
            showBarberName={state.barberId === null}
            slots={slots}
          />
        ) : null}

        {state.step === 3 ? (
          <StepConfirm
            chosenExtras={chosenExtras}
            isAuthenticated={isAuthenticated}
            isSessionReady={isReady}
            notes={notes}
            onNotesChange={setNotes}
            onPaymentMethodChange={setPaymentMethod}
            paymentMethod={paymentMethod}
            serviceName={selectedService?.name}
            slot={state.slot}
            submitError={submitError}
            totalCents={totalCents}
            totalMinutes={totalMinutes}
          />
        ) : null}
      </div>

      <BookingFooter
        canContinue={
          state.step === 0
            ? Boolean(state.serviceId)
            : state.step === 2
              ? Boolean(state.slot)
              : true
        }
        isAuthenticated={isAuthenticated}
        isSubmitting={isSubmitting}
        onBack={() => actions.goTo(Math.max(state.step - 1, 0))}
        onConfirm={() => void handleConfirm()}
        onNext={() =>
          actions.goTo(Math.min(state.step + 1, bookingSteps.length - 1))
        }
        step={state.step}
        totalCents={totalCents}
        totalMinutes={totalMinutes}
      />
    </Card>
  );
}
