import { apiRequest } from "@/lib/api-client";
import type {
  BarberRead,
  ProductExtraRead,
  ServiceRead,
} from "@/types/domain";

export function listServices() {
  return apiRequest<ServiceRead[]>("/api/v1/catalog/services");
}

export function listExtras() {
  return apiRequest<ProductExtraRead[]>("/api/v1/catalog/extras");
}

export function listBarbers() {
  return apiRequest<BarberRead[]>("/api/v1/users/barbers");
}

export function listAllServices(token: string) {
  return apiRequest<ServiceRead[]>("/api/v1/catalog/admin/services", {
    token,
  });
}

export function listAllExtras(token: string) {
  return apiRequest<ProductExtraRead[]>("/api/v1/catalog/admin/extras", {
    token,
  });
}

export function listAllBarbers(token: string) {
  return apiRequest<BarberRead[]>("/api/v1/users/admin/barbers", { token });
}

export type ServiceInput = {
  name: string;
  description?: string | null;
  duration_minutes: number;
  price_cents: number;
};

export function createService(token: string, input: ServiceInput) {
  return apiRequest<ServiceRead>("/api/v1/catalog/services", {
    method: "POST",
    token,
    body: input,
  });
}

export function updateService(
  token: string,
  id: string,
  input: Partial<ServiceInput> & { is_active?: boolean },
) {
  return apiRequest<ServiceRead>(`/api/v1/catalog/services/${id}`, {
    method: "PATCH",
    token,
    body: input,
  });
}

export type ExtraInput = {
  name: string;
  description?: string | null;
  duration_minutes: number;
  price_cents: number;
};

export function createExtra(token: string, input: ExtraInput) {
  return apiRequest<ProductExtraRead>("/api/v1/catalog/extras", {
    method: "POST",
    token,
    body: input,
  });
}

export function updateExtra(
  token: string,
  id: string,
  input: Partial<ExtraInput> & { is_active?: boolean },
) {
  return apiRequest<ProductExtraRead>(`/api/v1/catalog/extras/${id}`, {
    method: "PATCH",
    token,
    body: input,
  });
}

export type BarberInput = {
  email: string;
  password: string;
  display_name: string;
  bio?: string | null;
  phone?: string | null;
};

export function createBarber(token: string, input: BarberInput) {
  return apiRequest<BarberRead>("/api/v1/users/barbers", {
    method: "POST",
    token,
    body: input,
  });
}

export function updateBarber(
  token: string,
  id: string,
  input: {
    display_name?: string;
    bio?: string | null;
    phone?: string | null;
    is_active?: boolean;
  },
) {
  return apiRequest<BarberRead>(`/api/v1/users/barbers/${id}`, {
    method: "PATCH",
    token,
    body: input,
  });
}
