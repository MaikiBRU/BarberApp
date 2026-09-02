import { apiRequest } from "@/lib/api-client";
import type {
  AppointmentRead,
  AppointmentStatus,
  AvailabilityResponse,
  Page,
  PaymentMethod,
} from "@/types/domain";

export type AvailabilityInput = {
  serviceId: string;
  date: string;
  barberId?: string;
  extraIds?: string[];
};

export function fetchAvailability(input: AvailabilityInput) {
  return apiRequest<AvailabilityResponse>(
    "/api/v1/appointments/availability",
    {
      query: {
        service_id: input.serviceId,
        date: input.date,
        barber_id: input.barberId,
        extra_ids: input.extraIds,
      },
    },
  );
}

export type CreateAppointmentInput = {
  barber_id: string;
  service_id: string;
  starts_at: string;
  extra_ids?: string[];
  payment_method?: PaymentMethod;
  notes?: string;
};

export function createAppointment(
  token: string,
  input: CreateAppointmentInput,
) {
  return apiRequest<AppointmentRead>("/api/v1/appointments", {
    method: "POST",
    token,
    body: input,
  });
}

export type ListAppointmentsInput = {
  statuses?: AppointmentStatus[];
  barberId?: string;
  dateFrom?: string;
  dateTo?: string;
  limit?: number;
  offset?: number;
  newestFirst?: boolean;
};

export function listAppointments(
  token: string,
  input: ListAppointmentsInput = {},
) {
  return apiRequest<Page<AppointmentRead>>("/api/v1/appointments", {
    token,
    query: {
      status_filter: input.statuses,
      barber_id: input.barberId,
      date_from: input.dateFrom,
      date_to: input.dateTo,
      limit: input.limit ?? 50,
      offset: input.offset ?? 0,
      newest_first: input.newestFirst,
    },
  });
}

export function fetchAppointment(token: string, id: string) {
  return apiRequest<AppointmentRead>(`/api/v1/appointments/${id}`, { token });
}

export function updateAppointmentStatus(
  token: string,
  id: string,
  status: AppointmentStatus,
  cancellationReason?: string,
) {
  return apiRequest<AppointmentRead>(
    `/api/v1/appointments/${id}/status`,
    {
      method: "PATCH",
      token,
      body: {
        status,
        cancellation_reason: cancellationReason || undefined,
      },
    },
  );
}
