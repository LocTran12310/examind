import { keepPreviousData, useQuery, type UseQueryResult } from "@tanstack/react-query";
import type { SearchBody } from "@/dtos/search.dto";
import type { RowsQueryOptions, SearchPage } from "@/interfaces/search-page.interface";

/** A search list query: previous page kept while the next loads, optional polling. */
export function useSearchQuery<T>(
  queryKey: readonly unknown[],
  queryFn: (body: SearchBody) => Promise<SearchPage<T>>,
  body: SearchBody,
  options: RowsQueryOptions<T> & { enabled?: boolean } = {},
): UseQueryResult<SearchPage<T>, Error> {
  const { refetchInterval, enabled } = options;
  return useQuery<SearchPage<T>, Error>({
    queryKey,
    queryFn: () => queryFn(body),
    placeholderData: keepPreviousData,
    enabled,
    refetchInterval: typeof refetchInterval === "function" ? (q) => refetchInterval(q.state.data) : refetchInterval,
  });
}
