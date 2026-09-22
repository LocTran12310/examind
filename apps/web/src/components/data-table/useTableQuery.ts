"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useCallback, useMemo } from "react";

export type SortState = { key: string; desc: boolean } | null;

export const RESERVED = ["q", "sort", "page", "page_size"] as const;
export const PAGE_SIZES = [20, 50, 100] as const;

/**
 * Table state lives in the URL (ui-shadcn-shell ADR-02). `prefix` namespaces the params when a page
 * shows more than one table and must end with "." (e.g. `d.page` for a detail table).
 * Typing uses router.replace, paging uses router.push so Back walks through pages.
 */
export function useTableQuery(prefix = "") {
  const search = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();
  const k = useCallback((name: string) => prefix + name, [prefix]);

  const get = useCallback((name: string) => search.get(k(name)) ?? "", [search, k]);
  const page = Math.max(1, Number(get("page")) || 1);
  const pageSize = Number(get("page_size")) || PAGE_SIZES[0];
  const sortRaw = get("sort");
  const sort: SortState = sortRaw ? { key: sortRaw.replace(/^-/, ""), desc: sortRaw.startsWith("-") } : null;

  /** Params for the API request: this table's params without the prefix. */
  const apiParams = useMemo(() => {
    const out = new URLSearchParams();
    search.forEach((v, key) => {
      if (!key.startsWith(prefix) || v === "") return;
      const bare = key.slice(prefix.length);
      if (bare.includes(".")) return; // another table's params (prefixes end with ".")
      out.set(bare, v);
    });
    out.set("page", String(page));
    out.set("page_size", String(pageSize));
    return out;
  }, [search, prefix, page, pageSize]);

  const update = useCallback(
    (changes: Record<string, string | number | null | undefined>, opts: { push?: boolean; keepPage?: boolean } = {}) => {
      const next = new URLSearchParams(search.toString());
      for (const [name, value] of Object.entries(changes)) {
        if (value === null || value === undefined || value === "") next.delete(k(name));
        else next.set(k(name), String(value));
      }
      if (!opts.keepPage && !("page" in changes)) next.delete(k("page"));
      const qs = next.toString();
      const url = qs ? `${pathname}?${qs}` : pathname;
      if (opts.push) router.push(url, { scroll: false });
      else router.replace(url, { scroll: false });
    },
    [search, router, pathname, k],
  );

  return {
    get,
    page,
    pageSize,
    sort,
    apiParams,
    setFilter: (name: string, value: string | null) => update({ [name]: value }),
    setFilters: (changes: Record<string, string | null>) => update(changes),
    setPage: (p: number) => update({ page: p <= 1 ? null : p }, { push: true }),
    setPageSize: (size: number) => update({ page_size: size === PAGE_SIZES[0] ? null : size, page: null }, { push: true }),
    setSort: (s: SortState) => update({ sort: s ? (s.desc ? "-" : "") + s.key : null }, { keepPage: false }),
    clear: (names: string[]) => update(Object.fromEntries(names.map((n) => [n, null]))),
  };
}
