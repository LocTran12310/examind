/** Answer of `POST /<resource>/search`. */
export interface SearchPage<T> {
  data: T[];
  total: number;
  page: number;
  limit: number;
}

/** What a search query hook returns (the part of a React Query result a table needs). */
export interface RowsQuery<T> {
  data?: SearchPage<T>;
  isFetching: boolean;
  error: unknown;
  refetch: () => Promise<unknown>;
}

export interface RowsQueryOptions<T = unknown> {
  /** ms between refetches, or a function of the last page (false = stop) */
  refetchInterval?: number | false | ((page: SearchPage<T> | undefined) => number | false);
}
