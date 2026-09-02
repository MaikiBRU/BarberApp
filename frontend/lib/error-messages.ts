import { ApiError } from "@/lib/api-client";

/**
 * Turn any thrown value into a message a person can act on.
 *
 * Backend messages are already user-facing and never contain internals,
 * so they are passed through; anything else falls back to a generic
 * line rather than leaking a stack trace into the UI.
 */
export function toMessage(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.isNetworkFailure) {
      return "No se pudo conectar con el servidor. Revisa tu conexion e intenta de nuevo.";
    }
    if (error.status === 401) {
      return "Tu sesion expiro. Inicia sesion nuevamente.";
    }
    if (error.status >= 500) {
      return "El servidor tuvo un problema. Intenta de nuevo en unos minutos.";
    }
    return error.message;
  }

  if (error instanceof Error && error.message) {
    return error.message;
  }

  return "Ocurrio un error inesperado.";
}

/** Map field-level backend errors onto form field names. */
export function toFieldErrors(error: unknown): Record<string, string> {
  if (!(error instanceof ApiError)) {
    return {};
  }
  return Object.fromEntries(
    error.fieldErrors.map((item) => [item.field, item.message]),
  );
}
