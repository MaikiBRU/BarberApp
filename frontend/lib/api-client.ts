/**
 * Typed fetch wrapper around the BarberApp API.
 *
 * Every backend error uses one envelope, so failures are surfaced as a
 * single `ApiError` carrying the status, a machine-readable type and a
 * message the UI can show. Network failures are distinguished from HTTP
 * failures, which is what lets screens tell "no data" apart from "the
 * request failed".
 */

export type ApiErrorType =
  | "validation_error"
  | "authentication_error"
  | "authorization_error"
  | "not_found"
  | "conflict"
  | "slot_unavailable"
  | "business_rule_error"
  | "rate_limit_exceeded"
  | "database_unavailable"
  | "network_error"
  | "internal_error"
  | "http_error";

export type FieldError = {
  field: string;
  message: string;
  type: string;
};

type ErrorEnvelope = {
  error?: {
    type?: string;
    message?: string;
    details?: unknown;
  };
};

export class ApiError extends Error {
  readonly status: number;
  readonly type: ApiErrorType;
  readonly details: unknown;

  constructor(
    message: string,
    status: number,
    type: ApiErrorType,
    details: unknown = null,
  ) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.type = type;
    this.details = details;
  }

  /** True when the session is missing or has expired. */
  get isUnauthenticated(): boolean {
    return this.status === 401;
  }

  /** True when the API could not be reached at all. */
  get isNetworkFailure(): boolean {
    return this.type === "network_error";
  }

  /** Field-level messages, when the backend reported any. */
  get fieldErrors(): FieldError[] {
    if (!Array.isArray(this.details)) {
      return [];
    }
    return this.details.filter(
      (item): item is FieldError =>
        typeof item === "object" &&
        item !== null &&
        "field" in item &&
        "message" in item,
    );
  }
}

export const apiBaseUrl = (
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"
).replace(/\/$/, "");

type RequestOptions = {
  method?: "GET" | "POST" | "PATCH" | "PUT" | "DELETE";
  body?: unknown;
  /**
   * Bearer token. Defaults to the active session, which matters for the
   * endpoints that are public but tenant-aware: a demo visitor must see
   * their sandbox's catalog, barbers and hours, not the real shop's.
   * Pass `null` to force an anonymous request.
   */
  token?: string | null;
  query?: Record<string, string | number | boolean | string[] | undefined>;
  signal?: AbortSignal;
};

/** Read the stored session token without importing the store eagerly. */
function activeToken(): string | null {
  if (typeof window === "undefined") {
    return null;
  }
  try {
    const raw = window.localStorage.getItem("barberapp.session");
    if (!raw) return null;
    const parsed = JSON.parse(raw) as {
      token?: string;
      expiresAt?: number;
    };
    if (!parsed?.token || !parsed?.expiresAt) return null;
    return parsed.expiresAt > Date.now() ? parsed.token : null;
  } catch {
    return null;
  }
}

function buildQuery(query: RequestOptions["query"]): string {
  if (!query) {
    return "";
  }

  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(query)) {
    if (value === undefined || value === "") {
      continue;
    }
    if (Array.isArray(value)) {
      value.forEach((item) => params.append(key, item));
    } else {
      params.append(key, String(value));
    }
  }

  const serialized = params.toString();
  return serialized ? `?${serialized}` : "";
}

function toApiError(status: number, body: ErrorEnvelope | null): ApiError {
  const envelope = body?.error;
  const type = (envelope?.type ?? "http_error") as ApiErrorType;
  const message =
    envelope?.message ?? `The request failed with status ${status}.`;
  return new ApiError(message, status, type, envelope?.details ?? null);
}

export async function apiRequest<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const { method = "GET", body, query, signal } = options;
  const token =
    options.token === undefined ? activeToken() : options.token;

  const headers = new Headers({ Accept: "application/json" });
  if (body !== undefined) {
    headers.set("Content-Type", "application/json");
  }
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  let response: Response;
  try {
    response = await fetch(`${apiBaseUrl}${path}${buildQuery(query)}`, {
      method,
      headers,
      signal,
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw error;
    }
    throw new ApiError(
      "No se pudo conectar con el servidor. Revisá tu conexión e intentá de nuevo.",
      0,
      "network_error",
    );
  }

  if (response.status === 204) {
    return undefined as T;
  }

  const payload = (await response.json().catch(() => null)) as
    | ErrorEnvelope
    | null;

  if (!response.ok) {
    throw toApiError(response.status, payload);
  }

  return payload as T;
}
