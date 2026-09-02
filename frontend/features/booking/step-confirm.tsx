"use client";

import { SelectField, TextareaField } from "@/components/ui/field";
import { FormMessage } from "@/components/ui/states";
import type { SlotChoice } from "@/features/booking/use-booking-state";
import { formatDateTime, formatDuration, formatPrice } from "@/lib/format";
import { paymentMethodLabels } from "@/lib/status";
import type { PaymentMethod, ProductExtraRead } from "@/types/domain";

type StepConfirmProps = {
  serviceName?: string;
  chosenExtras: ProductExtraRead[];
  slot: SlotChoice | null;
  totalCents: number;
  totalMinutes: number;
  paymentMethod: PaymentMethod;
  onPaymentMethodChange: (method: PaymentMethod) => void;
  notes: string;
  onNotesChange: (notes: string) => void;
  isAuthenticated: boolean;
  isSessionReady: boolean;
  submitError: string | null;
};

export function StepConfirm({
  serviceName,
  chosenExtras,
  slot,
  totalCents,
  totalMinutes,
  paymentMethod,
  onPaymentMethodChange,
  notes,
  onNotesChange,
  isAuthenticated,
  isSessionReady,
  submitError,
}: StepConfirmProps) {
  return (
    <div className="space-y-5">
      <dl className="divide-y divide-line rounded-md border border-line text-sm">
        <SummaryRow label="Servicio" value={serviceName} />
        <SummaryRow
          label="Extras"
          value={
            chosenExtras.length
              ? chosenExtras.map((extra) => extra.name).join(", ")
              : "Sin extras"
          }
        />
        <SummaryRow label="Barbero" value={slot?.barberName} />
        <SummaryRow
          label="Fecha y hora"
          value={slot ? formatDateTime(slot.startsAt) : undefined}
        />
        <SummaryRow label="Duración" value={formatDuration(totalMinutes)} />
        <SummaryRow label="Total estimado" value={formatPrice(totalCents)} />
      </dl>

      <SelectField
        label="Método de pago"
        onChange={(event) =>
          onPaymentMethodChange(event.target.value as PaymentMethod)
        }
        value={paymentMethod}
      >
        {Object.entries(paymentMethodLabels).map(([value, label]) => (
          <option key={value} value={value}>
            {label}
          </option>
        ))}
      </SelectField>

      <TextareaField
        hint="Opcional. Contanos algo que el barbero deba saber."
        label="Notas"
        maxLength={1000}
        onChange={(event) => onNotesChange(event.target.value)}
        value={notes}
      />

      {isSessionReady && !isAuthenticated ? (
        <FormMessage tone="error">
          Iniciá sesión para confirmar la reserva.
        </FormMessage>
      ) : null}
      {submitError ? (
        <FormMessage tone="error">{submitError}</FormMessage>
      ) : null}
    </div>
  );
}

function SummaryRow({ label, value }: { label: string; value?: string }) {
  return (
    <div className="flex items-center justify-between gap-4 px-4 py-2.5">
      <dt className="text-ink-muted">{label}</dt>
      <dd className="text-right font-medium">{value ?? "-"}</dd>
    </div>
  );
}
