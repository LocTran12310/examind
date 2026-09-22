import { vi } from "vitest";

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
    return jsonResponse(404, { error: { code: "not_found", message: "not mocked: " + url } });
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

export const me = (role: import("@/lib/types").Role = "org_admin", o: Partial<import("@/lib/types").Me> = {}): import("@/lib/types").Me => ({
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

export const page = <T,>(items: T[], total = items.length, pageNo = 1, size = 20) => ({ items, total, page: pageNo, page_size: size });
