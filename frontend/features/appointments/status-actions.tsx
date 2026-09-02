"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { FormMessage } from "@/components/ui/states";
import { useSession } from "@/hooks/use-session";
import { toMessage } from "@/lib/error-messages";
import { transitionLabels } from "@/lib/status";
import { updateAppointmentStatus } from "@/services/appointments";
import type { AppointmentRead, AppointmentStatus } from "@/types/domain";

type StatusActionsProps = {
  appointment: AppointmentRead;
  size?: "sm" | "md";
};

/**
 * Render only the transitions the API says this viewer may perform.
 *
 * The list comes from `allowed_transitions`, so the UI never offers an
 * action the server would reject.
 */
export function StatusActions({
  appointment,
  size = "sm",
}: StatusActionsProps) {
  const { token } = useSession();
  const queryClient = useQueryClient();
  const [pendingStatus, setPendingStatus] =
    useState<AppointmentStatus | null>(null);

  const mutation = useMutation({
    mutationFn: (status: AppointmentStatus) =>
      updateAppointmentStatus(
        token as string,
        appointment.id,
        status,
        status === "cancelled" ? "Cancelado desde la aplicacion" : undefined,
      ),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["appointments"] });
      void queryClient.invalidateQueries({ queryKey: ["appointment"] });
      void queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      void queryClient.invalidateQueries({ queryKey: ["availability"] });
    },
    onSettled: () => setPendingStatus(null),
  });

  if (appointment.allowed_transitions.length === 0) {
    return null;
  }

  return (
    <div className="space-y-2">
      <div className="flex flex-wrap gap-2">
        {appointment.allowed_transitions.map((status) => (
          <Button
            isLoading={
              mutation.isPending && pendingStatus === status
            }
            key={status}
            onClick={() => {
              setPendingStatus(status);
              mutation.mutate(status);
            }}
            size={size}
            variant={status === "cancelled" ? "danger" : "secondary"}
          >
            {transitionLabels[status]}
          </Button>
        ))}
      </div>
      {mutation.isError ? (
        <FormMessage tone="error">{toMessage(mutation.error)}</FormMessage>
      ) : null}
    </div>
  );
}
