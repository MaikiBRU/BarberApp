import { apiRequest } from "@/lib/api-client";
import type { AuthResponse, UserRead } from "@/types/domain";

export type LoginInput = {
  email: string;
  password: string;
};

export type RegisterInput = LoginInput & {
  full_name?: string;
  phone?: string;
};

export function login(input: LoginInput) {
  return apiRequest<AuthResponse>("/api/v1/auth/login", {
    method: "POST",
    body: input,
  });
}

export function register(input: RegisterInput) {
  return apiRequest<AuthResponse>("/api/v1/auth/register", {
    method: "POST",
    body: input,
  });
}

export function fetchMe(token: string) {
  return apiRequest<UserRead>("/api/v1/auth/me", { token });
}
