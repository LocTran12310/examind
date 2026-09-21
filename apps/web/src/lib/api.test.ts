import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { api, ApiError } from "./api";

const json = (status: number, body: unknown) =>
  new Response(body === undefined ? null : JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  });

describe("api client", () => {
  const fetchMock = vi.fn();
  beforeEach(() => {
    fetchMock.mockReset();
    vi.stubGlobal("fetch", fetchMock);
  });
  afterEach(() => vi.unstubAllGlobals());

  it("refreshes once on 401 then retries", async () => {
    fetchMock
      .mockResolvedValueOnce(json(401, { error: { code: "unauthenticated", message: "x" } }))
      .mockResolvedValueOnce(new Response(null, { status: 204 }))
      .mockResolvedValueOnce(json(200, { ok: true }));
    await expect(api("/auth/me")).resolves.toEqual({ ok: true });
    expect(fetchMock.mock.calls.map((c) => c[0])).toEqual(["/api/auth/me", "/api/auth/refresh", "/api/auth/me"]);
  });

  it("throws ApiError with code and fields", async () => {
    fetchMock.mockResolvedValueOnce(
      json(422, { error: { code: "validation_error", message: "bad", fields: { code: "sai" } } }),
    );
    const err = await api("/admin/orgs", { body: {} }).catch((e) => e);
    expect(err).toBeInstanceOf(ApiError);
    expect(err.code).toBe("validation_error");
    expect(err.fields).toEqual({ code: "sai" });
  });

  it("does not refresh for login failures", async () => {
    fetchMock.mockResolvedValueOnce(json(401, { error: { code: "invalid_credentials", message: "Sai" } }));
    await expect(api("/auth/login", { body: {} })).rejects.toMatchObject({ code: "invalid_credentials" });
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });
});
