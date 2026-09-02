"use client";

import Link from "next/link";

import { Button } from "@/components/ui/button";
import { bookingSteps } from "@/features/booking/stepper";
import { formatDuration, formatPrice } from "@/lib/format";
import { routes } from "@/lib/routes";

type BookingFooterProps = {
  step: number;
  canContinue: boolean;
  isAuthenticated: boolean;
  isSubmitting: boolean;
  totalCents: number;
  totalMinutes: number;
  onBack: () => void;
  onNext: () => void;
  onConfirm: () => void;
};

export function BookingFooter({
  step,
  canContinue,
  isAuthenticated,
  isSubmitting,
  totalCents,
  totalMinutes,
  onBack,
  onNext,
  onConfirm,
}: BookingFooterProps) {
  const isLast = step === bookingSteps.length - 1;

  return (
    <div className="flex flex-wrap items-center justify-between gap-3 border-t border-line px-4 py-4 sm:px-5">
      <p className="text-sm text-ink-muted">
        {totalMinutes > 0 ? (
          <>
            <span className="font-medium text-ink">
              {formatPrice(totalCents)}
            </span>{" "}
            &middot; {formatDuration(totalMinutes)}
          </>
        ) : (
          "Elegí un servicio para continuar"
        )}
      </p>
      <div className="flex gap-2">
        {step > 0 ? (
          <Button onClick={onBack} variant="secondary">
            Atrás
          </Button>
        ) : null}
        {isLast ? (
          isAuthenticated ? (
            <Button isLoading={isSubmitting} onClick={onConfirm}>
              Confirmar reserva
            </Button>
          ) : (
            <Link href={routes.login}>
              <Button>Iniciar sesión</Button>
            </Link>
          )
        ) : (
          <Button disabled={!canContinue} onClick={onNext}>
            Continuar
          </Button>
        )}
      </div>
    </div>
  );
}
