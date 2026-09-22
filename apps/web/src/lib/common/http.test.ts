import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError, http as api } from "./http";

const json = (status: number, body: unknown) =>
  new Response(body === undefined ? null : JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  });

describe("http client", () => {
  const fetchMock = vi.fn();
  beforeEach(() => {
    fetchMock.mockReset();
    vi.stubGlobal("fetch", fetchMock);
  });
  afterEach(() => vi.unstubAllGlobals());

  it("refreshes once on 401 then retries", async () => {
    fetchMock
      .mockResolvedValueOnce(json(401, { code: "unauthenticated", message: "x" }))
      .mockResolvedValueOnce(new Response(null, { status: 204 }))
      .mockResolvedValueOnce(json(200, { ok: true }));
    await expect(api("/auth/me")).resolves.toEqual({ ok: true });
    expect(fetchMock.mock.calls.map((c) => c[0])).toEqual(["/api/auth/me", "/api/auth/refresh", "/api/auth/me"]);
  });

  it("throws ApiError with code and fields", async () => {
    fetchMock.mockResolvedValueOnce(
      json(422, { code: "validation_error", message: "bad", details: { fields: { code: "sai" }, requestId: "r1" } }),
    );
    const err = (await api("/admin/orgs", { body: {} }).catch((e) => e)) as ApiError;
    expect(err).toBeInstanceOf(ApiError);
    expect(err.code).toBe("validation_error");
    expect(err.fields).toEqual({ code: "sai" });
    expect(err.requestId).toBe("r1");
  });

  it("does not refresh for login failures", async () => {
    fetchMock.mockResolvedValueOnce(json(401, { code: "invalid_credentials", message: "Sai" }));
    await expect(api("/auth/login", { body: {} })).rejects.toMatchObject({ code: "invalid_credentials" });
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });
});
