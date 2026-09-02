import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiError, apiRequest } from "@/lib/api-client";

function mockFetch(response: Partial<Response> & { json?: () => unknown }) {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({
      ok: response.ok ?? true,
      status: response.status ?? 200,
      json: response.json ?? (() => Promise.resolve({})),
    }),
  );
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("apiRequest", () => {
  it("returns the parsed payload on success", async () => {
    mockFetch({
      status: 200,
      json: () => Promise.resolve({ id: "abc" }),
    });

    await expect(apiRequest<{ id: string }>("/x")).resolves.toEqual({
      id: "abc",
    });
  });

  it("returns undefined for an empty 204 response", async () => {
    mockFetch({ status: 204 });

    await expect(apiRequest("/x")).resolves.toBeUndefined();
  });

  it("maps the error envelope onto a typed ApiError", async () => {
    mockFetch({
      ok: false,
      status: 409,
      json: () =>
        Promise.resolve({
          error: {
            type: "slot_unavailable",
            message: "El horario ya no está disponible",
            details: null,
          },
        }),
    });

    const error = await apiRequest("/x").catch((thrown) => thrown);

    expect(error).toBeInstanceOf(ApiError);
    expect((error as ApiError).status).toBe(409);
    expect((error as ApiError).type).toBe("slot_unavailable");
    expect((error as ApiError).message).toBe(
      "El horario ya no está disponible",
    );
  });

  it("exposes field errors from a validation response", async () => {
    mockFetch({
      ok: false,
      status: 422,
      json: () =>
        Promise.resolve({
          error: {
            type: "validation_error",
            message: "Datos inválidos",
            details: [
              { field: "email", message: "Email inválido", type: "value" },
            ],
          },
        }),
    });

    const error = (await apiRequest("/x").catch(
      (thrown) => thrown,
    )) as ApiError;

    expect(error.fieldErrors).toEqual([
      { field: "email", message: "Email inválido", type: "value" },
    ]);
  });

  it("distinguishes a network failure from an HTTP failure", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockRejectedValue(new TypeError("Failed to fetch")),
    );

    const error = (await apiRequest("/x").catch(
      (thrown) => thrown,
    )) as ApiError;

    expect(error.isNetworkFailure).toBe(true);
    expect(error.status).toBe(0);
  });

  it("flags 401 responses so the UI can prompt a new login", async () => {
    mockFetch({
      ok: false,
      status: 401,
      json: () =>
        Promise.resolve({
          error: { type: "authentication_error", message: "No autorizado" },
        }),
    });

    const error = (await apiRequest("/x").catch(
      (thrown) => thrown,
    )) as ApiError;

    expect(error.isUnauthenticated).toBe(true);
  });
});
