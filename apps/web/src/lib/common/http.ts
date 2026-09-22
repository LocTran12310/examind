/** HTTP client of the app: `services/*` are its only callers (architecture-refactor ADR-06).
 *  Cookies carry the session; a 401 refreshes once and retries; errors arrive as
 *  `{code, message, details: {fields?, requestId}}` (ADR-04). */
export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string,
    public fields?: Record<string, string>,
    public requestId?: string,
  ) {
    super(message);
  }
}

type Options = {
  method?: string;
  body?: unknown;
  form?: FormData;
  /** internal: set after one refresh attempt */
  retried?: boolean;
};

let refreshing: Promise<boolean> | null = null;

async function refreshOnce(): Promise<boolean> {
  refreshing ??= fetch("/api/auth/refresh", { method: "POST", credentials: "include" })
    .then((r) => r.ok)
    .catch(() => false)
    .finally(() => {
      setTimeout(() => (refreshing = null), 0);
    });
  return refreshing;
}

export function onUnauthenticated() {
  if (typeof window !== "undefined" && !window.location.pathname.startsWith("/login")) {
    window.location.assign("/login");
  }
}

export async function http<T = unknown>(path: string, opts: Options = {}): Promise<T> {
  const init: RequestInit = { method: opts.method ?? (opts.body || opts.form ? "POST" : "GET"), credentials: "include" };
  if (opts.form) init.body = opts.form;
  else if (opts.body !== undefined) {
    init.body = JSON.stringify(opts.body);
    init.headers = { "content-type": "application/json" };
  }
  const res = await fetch(`/api${path}`, init);
  if (res.status === 401 && !opts.retried && !path.startsWith("/auth/login")) {
    if (await refreshOnce()) return http<T>(path, { ...opts, retried: true });
    onUnauthenticated();
  }
  if (res.status === 403) {
    const peek = await res.clone().json().catch(() => null);
    if (peek?.code === "password_change_required" && typeof window !== "undefined") {
      window.location.assign("/change-password");
    }
  }
  if (!res.ok) {
    const err = (await res.json().catch(() => null)) ?? {};
    throw new ApiError(res.status, err.code ?? "http_error", err.message ?? `Lỗi ${res.status}`, err.details?.fields, err.details?.requestId);
  }
  if (res.status === 204) return undefined as T;
  const type = res.headers.get("content-type") ?? "";
  return (type.includes("application/json") ? res.json() : res.blob()) as Promise<T>;
}

/** The old name, kept while the pre-refactor screens are moved to services. */
export const api = http;
