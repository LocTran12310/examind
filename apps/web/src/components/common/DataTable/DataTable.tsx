"use client";

import type { ColumnDef } from "@tanstack/react-table";
import { useMemo } from "react";
import type { SearchBody } from "@/dtos/search.dto";
import { useTableQuery } from "@/hooks/common/use-table-query";
import type { RowsQuery, RowsQueryOptions } from "@/interfaces/search-page.interface";
import { ApiError } from "@/lib/common/http";
import { type FilterKind, toSearchBody } from "@/lib/common/search-body";
import { type DataTableBaseProps, DataTableView } from "./DataTableView";

export interface DataTableProps<T> extends DataTableBaseProps<T> {
  /** The resource's search query hook, e.g. `useTagSearchQuery`; it gets the body built from the URL. */
  useRows: (body: SearchBody, options?: RowsQueryOptions<T>) => RowsQuery<T>;
  /** Resource parameters always sent in the body (e.g. `{ class_id }`), not shown in the URL. */
  params?: Record<string, unknown>;
  /** Refetch every 2 s while this returns true (e.g. documents still being processed). */
  refetchWhile?: (items: T[]) => boolean;
}

/** The URL param of a column filter: `meta.filter.key`, else the column id / accessor key. */
export function filterKinds<T>(columns: ColumnDef<T, unknown>[]): Record<string, FilterKind> {
  const out: Record<string, FilterKind> = {};
  for (const c of columns) {
    const spec = c.meta?.filter;
    if (!spec) continue;
    const key = spec.key ?? c.id ?? ("accessorKey" in c ? String(c.accessorKey) : "");
    if (key) out[key] = spec.param ? "param" : spec.kind;
  }
  return out;
}

/** Server-side table: URL state → search body → the resource's query hook → DataTableView. */
export function DataTable<T>({ useRows, params, refetchWhile, prefix = "", ...rest }: DataTableProps<T>) {
  const tq = useTableQuery(prefix);
  const kinds = useMemo(() => filterKinds(rest.columns), [rest.columns]);
  const body = useMemo(() => toSearchBody(tq.apiParams, kinds, params), [tq.apiParams, kinds, params]);
  const resetKey = JSON.stringify(body);
  const rows = useRows(body, { refetchInterval: refetchWhile ? (page) => (page && refetchWhile(page.data) ? 2000 : false) : false });
  const data = useMemo(() => (rows.data ? { items: rows.data.data, total: rows.data.total } : null), [rows.data]);
  const error = rows.error ? (rows.error instanceof ApiError ? rows.error.message : "Không tải được dữ liệu") : null;
  return <DataTableView {...rest} prefix={prefix} tq={tq} data={data} loading={rows.isFetching} error={error} reload={rows.refetch} resetKey={resetKey} />;
}
