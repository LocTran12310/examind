import { QueryClientProvider } from "@tanstack/react-query";
import { render, type RenderOptions } from "@testing-library/react";
import { vi } from "vitest";
import { makeQueryClient } from "@/lib/common/query-client";

type Handler = (url: string, init?: RequestInit) => { status?: number; body?: unknown } | undefined;

export function jsonResponse(status: number, body?: unknown) {
  return new Response(body === undefined ? null : JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  });
}

/** Stub fetch; each handler may return a response spec or undefined to fall through. */
export function mockFetch(...handlers: Handler[]) {
  const fn = vi.fn(async (url: string, init?: RequestInit) => {
    for (const h of handlers) {
      const r = h(String(url), init);
      if (r) return jsonResponse(r.status ?? 200, r.body);
    }
    return jsonResponse(404, { code: "not_found", message: "not mocked: " + url });
  });
  vi.stubGlobal("fetch", fn);
  return fn;
}

export const route =
  (method: string, pattern: string | RegExp, body: unknown, status = 200): Handler =>
  (url, init) => {
    const m = (init?.method ?? "GET").toUpperCase();
    const hit = typeof pattern === "string" ? url === pattern : pattern.test(url);
    return m === method && hit ? { status, body } : undefined;
  };

export const me = (role: import("@/interfaces/auth.interface").Role = "org_admin", o: Partial<import("@/interfaces/auth.interface").Me> = {}): import("@/interfaces/auth.interface").Me => ({
  id: "me",
  username: "admin",
  full_name: "Quản Trị",
  role,
  must_change_password: false,
  org: { id: "o1", code: "trungtama", name: "Trung tâm A" },
  ...o,
});

/** Last request to a path, as URLSearchParams. */
export function lastQuery(fetch: { mock: { calls: unknown[][] } }, path: string): URLSearchParams {
  const call = [...fetch.mock.calls].reverse().find((c) => String(c[0]).startsWith(`/api${path}?`) || String(c[0]) === `/api${path}`);
  if (!call) throw new Error(`no request to ${path}`);
  return new URL(String(call[0]), "http://x").searchParams;
}

/** Search answer (`POST /<resource>/search`). */
export const searchPage = <T,>(data: T[], total = data.length, pageNo = 1, limit = 20) => ({ data, total, page: pageNo, limit });

/** Body of the last POST to a path. */
export function lastBody(fetch: { mock: { calls: unknown[][] } }, path: string): Record<string, unknown> {
  const call = [...fetch.mock.calls].reverse().find((c) => String(c[0]) === `/api${path}` && (c[1] as RequestInit | undefined)?.method === "POST");
  if (!call) throw new Error(`no POST to ${path}`);
  return JSON.parse(String((call[1] as RequestInit).body));
}

/** Render inside a fresh QueryClient (no retries, nothing shared between tests). */
export function renderWithQuery(ui: React.ReactElement, options?: RenderOptions) {
  const client = makeQueryClient();
  client.setDefaultOptions({ queries: { retry: false, staleTime: 0, refetchOnWindowFocus: false } });
  return { client, ...render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>, options) };
}
