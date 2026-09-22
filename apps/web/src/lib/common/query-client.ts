import { isServer, QueryClient } from "@tanstack/react-query";

/** One QueryClient per browser tab (architecture-refactor ADR-06): data is stale at once, one retry,
 *  no refetch on window focus. The server renders with a throw-away client. */
export function makeQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: { queries: { staleTime: 0, retry: 1, refetchOnWindowFocus: false } },
  });
}

let browserClient: QueryClient | undefined;

export function getQueryClient(): QueryClient {
  if (isServer) return makeQueryClient();
  browserClient ??= makeQueryClient();
  return browserClient;
}

/** Refresh every query of these resources (their `<ENTITY>_KEYS.ALL`). */
export function invalidate(qc: QueryClient, ...keys: readonly (readonly unknown[])[]): Promise<void> {
  return Promise.all(keys.map((queryKey) => qc.invalidateQueries({ queryKey }))).then(() => undefined);
}
