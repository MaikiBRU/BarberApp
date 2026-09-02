import { apiRequest } from "@/lib/api-client";
import type {
  DemoConfig,
  DemoSessionRead,
  DemoStartResponse,
  UserRole,
} from "@/types/domain";

export function fetchDemoConfig() {
  return apiRequest<DemoConfig>("/api/v1/demo/config");
}

export function startDemoSession() {
  return apiRequest<DemoStartResponse>("/api/v1/demo/session", {
    method: "POST",
  });
}

export function readDemoSession(token: string) {
  return apiRequest<DemoSessionRead>("/api/v1/demo/session", { token });
}

export function switchDemoRole(token: string, role: UserRole) {
  return apiRequest<DemoStartResponse>("/api/v1/demo/session/role", {
    method: "POST",
    token,
    body: { role },
  });
}

export function resetDemoSession(token: string) {
  return apiRequest<DemoStartResponse>("/api/v1/demo/session/reset", {
    method: "POST",
    token,
  });
}

export function endDemoSession(token: string) {
  return apiRequest<{ status: string; removed: number }>(
    "/api/v1/demo/session/end",
    { method: "POST", token },
  );
}
