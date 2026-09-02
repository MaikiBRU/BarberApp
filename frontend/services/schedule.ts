import { apiRequest } from "@/lib/api-client";
import type { BusinessHours, TimeOff } from "@/types/domain";

export function listBusinessHours() {
  return apiRequest<BusinessHours[]>("/api/v1/schedule/business-hours");
}

export function replaceBusinessHours(
  token: string,
  days: BusinessHours[],
) {
  return apiRequest<BusinessHours[]>("/api/v1/schedule/business-hours", {
    method: "PUT",
    token,
    body: { days },
  });
}

export function listTimeOff(token: string, barberId: string) {
  return apiRequest<TimeOff[]>(
    `/api/v1/schedule/barbers/${barberId}/time-off`,
    { token },
  );
}

export function createTimeOff(
  token: string,
  barberId: string,
  input: { starts_at: string; ends_at: string; reason?: string },
) {
  return apiRequest<TimeOff>(
    `/api/v1/schedule/barbers/${barberId}/time-off`,
    { method: "POST", token, body: input },
  );
}

export function deleteTimeOff(
  token: string,
  barberId: string,
  timeOffId: string,
) {
  return apiRequest<void>(
    `/api/v1/schedule/barbers/${barberId}/time-off/${timeOffId}`,
    { method: "DELETE", token },
  );
}
