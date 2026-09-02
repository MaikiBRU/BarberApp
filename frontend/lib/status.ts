import type { AppointmentStatus, PaymentStatus } from "@/types/domain";

export type Tone =
  | "neutral"
  | "info"
  | "positive"
  | "warning"
  | "danger";

type StatusMeta = {
  label: string;
  tone: Tone;
};

export const appointmentStatusMeta: Record<AppointmentStatus, StatusMeta> = {
  pending: { label: "Pendiente", tone: "warning" },
  confirmed: { label: "Confirmado", tone: "info" },
  completed: { label: "Completado", tone: "positive" },
  cancelled: { label: "Cancelado", tone: "danger" },
  no_show: { label: "No asistió", tone: "neutral" },
};

export const paymentStatusMeta: Record<PaymentStatus, StatusMeta> = {
  pending: { label: "Pago pendiente", tone: "warning" },
  paid: { label: "Pagado", tone: "positive" },
  failed: { label: "Pago fallido", tone: "danger" },
  refunded: { label: "Reembolsado", tone: "neutral" },
};

export const transitionLabels: Record<AppointmentStatus, string> = {
  pending: "Marcar pendiente",
  confirmed: "Confirmar",
  completed: "Marcar completado",
  cancelled: "Cancelar",
  no_show: "Marcar como ausente",
};

export const weekdayLabels = [
  "Lunes",
  "Martes",
  "Miércoles",
  "Jueves",
  "Viernes",
  "Sábado",
  "Domingo",
] as const;

export const paymentMethodLabels = {
  cash: "Efectivo",
  transfer: "Transferencia",
  card: "Tarjeta",
  mercado_pago: "Mercado Pago",
} as const;
