"use client";

// Tables of screens not yet moved to query hooks: GET list path + reloadKey. Moved screens use
// components/common/DataTable/DataTable (search body + React Query).
import { useEffect, useMemo } from "react";
import { type DataTableBaseProps, DataTableView } from "@/components/common/DataTable/DataTableView";
import { useTableQuery } from "@/hooks/common/use-table-query";
import { useApi } from "@/lib/hooks";
import type { Page } from "@/lib/types";

export type { ToolbarContext } from "@/components/common/DataTable/DataTableView";

export interface DataTableProps<T> extends DataTableBaseProps<T> {
  /** API list path, e.g. "/users"; the URL's table params are appended. */
  path: string;
  /** Fixed params always sent (e.g. `{ class_id }`), not shown in the URL. */
  params?: Record<string, string | undefined>;
  /** Change this value to force a reload (e.g. after a dialog saved). */
  reloadKey?: unknown;
  /** Reload every 2 s while this returns true (e.g. documents still being processed). */
  pollWhile?: (items: T[]) => boolean;
}

export function DataTable<T>({ path, params, reloadKey, pollWhile, prefix = "", ...rest }: DataTableProps<T>) {
  const tq = useTableQuery(prefix);
  const query = useMemo(() => {
    const q = new URLSearchParams(tq.apiParams);
    for (const [k, v] of Object.entries(params ?? {})) if (v) q.set(k, v);
    return q.toString();
  }, [tq.apiParams, params]);
  const { data, error, loading, reload } = useApi<Page<T>>(`${path}${path.includes("?") ? "&" : "?"}${query}`);
  useEffect(() => {
    if (reloadKey === undefined) return;
    void reload();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [reloadKey]);
  const polling = !!(pollWhile && data && pollWhile(data.items));
  useEffect(() => {
    if (!polling) return;
    const t = setInterval(() => void reload(), 2000);
    return () => clearInterval(t);
  }, [polling, reload]);
  const view = useMemo(() => (data ? { items: data.items, total: data.total } : null), [data]);
  return <DataTableView {...rest} prefix={prefix} tq={tq} data={view} loading={loading} error={error} reload={reload} resetKey={`${query}|${String(reloadKey)}`} />;
}
