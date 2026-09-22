/**
 * In-memory Next router for tests: `vi.mock("next/navigation", () => routerMock)` then
 * `setUrl("/org/users?full_name=bui")`. replace/push update the URL and re-render hooks.
 */
import { useSyncExternalStore } from "react";
import { vi } from "vitest";

let url = new URL("http://test/");
const listeners = new Set<() => void>();
const emit = () => listeners.forEach((l) => l());

export function setUrl(path: string) {
  url = new URL(path, "http://test");
  emit();
}
export const currentUrl = () => url.pathname + url.search;
export const searchOf = () => new URLSearchParams(url.search);

const navigate = (to: string) => {
  url = new URL(to, "http://test");
  emit();
};
export const router = { push: vi.fn(navigate), replace: vi.fn(navigate), refresh: vi.fn(), back: vi.fn(), prefetch: vi.fn() };

function useUrl() {
  return useSyncExternalStore(
    (l) => (listeners.add(l), () => listeners.delete(l)),
    () => url.href,
  );
}

export const routerMock = {
  useRouter: () => router,
  usePathname: () => (useUrl(), url.pathname),
  useSearchParams: () => {
    const href = useUrl();
    return new URLSearchParams(new URL(href).search);
  },
  redirect: vi.fn(),
  notFound: vi.fn(),
};
