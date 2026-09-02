import { apiRequest } from "@/lib/api-client";
import type { AppointmentRead, DashboardSummary } from "@/types/domain";

export function fetchDashboardSummary(token: string) {
  return apiRequest<DashboardSummary>("/api/v1/dashboard/summary", { token });
}

export function fetchTodayAgenda(token: string) {
  return apiRequest<AppointmentRead[]>("/api/v1/dashboard/today", { token });
}
