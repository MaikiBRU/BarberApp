import { apiRequest } from "@/lib/api-client";
import type { CustomerProfile } from "@/types/domain";

export function fetchMyProfile(token: string) {
  return apiRequest<CustomerProfile>("/api/v1/users/me/profile", { token });
}

export function updateMyProfile(
  token: string,
  input: { full_name?: string | null; phone?: string | null },
) {
  return apiRequest<CustomerProfile>("/api/v1/users/me/profile", {
    method: "PATCH",
    token,
    body: input,
  });
}
