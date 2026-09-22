"use client";

import { type ColumnDef, flexRender, getCoreRowModel, type RowSelectionState, useReactTable } from "@tanstack/react-table";
import { ArrowDown, ArrowUp, ArrowUpDown, Pencil, Plus, RefreshCw, Trash2 } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { ConfirmDialog } from "@/components/app/ConfirmDialog";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableFooter, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { toast } from "sonner";
import { ApiError } from "@/lib/api";
import { useApi } from "@/lib/hooks";
import type { Page } from "@/lib/types";
import { cn } from "@/lib/utils";
import { FilterCell } from "./FilterCell";
import { Pagination } from "./Pagination";
import { Toolbar, ToolbarButton, ToolbarSeparator } from "./Toolbar";
import "./types";
import { useTableQuery } from "./useTableQuery";

export interface ToolbarContext<T> {
  selected: T[];
  reload: () => Promise<void>;
  clearSelection: () => void;
}

export interface DataTableProps<T> {
  /** API list path, e.g. "/users"; the URL's table params are appended. */
  path: string;
  columns: ColumnDef<T, unknown>[];
  getRowId: (row: T) => string;
  /** Fixed params always sent (e.g. `{ class_id }`), not shown in the URL. */
  params?: Record<string, string | undefined>;
  /** Namespace for the URL params when a page has several tables; must end with "." */
  prefix?: string;
  selectable?: boolean;
  onAdd?: () => void;
  addLabel?: string;
  onEdit?: (row: T) => void;
  onDelete?: (rows: T[]) => Promise<void> | void;
  deleteLabel?: (rows: T[]) => string;
  /** Extra toolbar buttons (use `ToolbarButton`). */
  actions?: (ctx: ToolbarContext<T>) => React.ReactNode;
  /** Row activated (click / Enter): e.g. open the detail panel or a page. */
  onRowActivate?: (row: T) => void;
  activeRowId?: string | null;
  footer?: (items: T[], total: number) => React.ReactNode;
  emptyText?: string;
  /** Change this value to force a reload (e.g. after a dialog saved). */
  reloadKey?: unknown;
  /** Reload every 2 s while this returns true (e.g. documents still being processed). */
  pollWhile?: (items: T[]) => boolean;
  rowClassName?: (row: T) => string | undefined;
  /** false = no toolbar (read-only detail tables) */
  toolbar?: boolean;
}

export function DataTable<T>({
  path,
  columns,
  getRowId,
  params,
  prefix = "",
  selectable = true,
  onAdd,
  addLabel = "Thêm mới",
  onEdit,
  onDelete,
  deleteLabel,
  actions,
  onRowActivate,
  activeRowId,
  footer,
  emptyText = "Không có dữ liệu",
  reloadKey,
  pollWhile,
  rowClassName,
  toolbar = true,
}: DataTableProps<T>) {
  const tq = useTableQuery(prefix);
  const query = useMemo(() => {
    const q = new URLSearchParams(tq.apiParams);
    for (const [k, v] of Object.entries(params ?? {})) if (v) q.set(k, v);
    return q.toString();
  }, [tq.apiParams, params]);
  const { data, error, loading, reload } = useApi<Page<T>>(`${path}${path.includes("?") ? "&" : "?"}${query}`);
  const [selection, setSelection] = useState<RowSelectionState>({});
  const [confirming, setConfirming] = useState(false);
  const items = useMemo(() => data?.items ?? [], [data]);
  const total = data?.total ?? 0;

  useEffect(() => setSelection({}), [query]);
  useEffect(() => {
    if (reloadKey === undefined) return;
    setSelection({});
    void reload();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [reloadKey]);
  const polling = !!(pollWhile && data && pollWhile(data.items));
  useEffect(() => {
    if (!polling) return;
    const t = setInterval(() => void reload(), 2000);
    return () => clearInterval(t);
  }, [polling, reload]);
  // A page past the end (rows deleted, stale link): jump to the last page.
  useEffect(() => {
    if (data && data.items.length === 0 && data.total > 0 && tq.page > 1) tq.setPage(Math.ceil(data.total / tq.pageSize));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data]);

  const allColumns = useMemo<ColumnDef<T, unknown>[]>(() => {
    if (!selectable) return columns;
    return [
      {
        id: "__select",
        header: ({ table }) => (
          <Checkbox
            aria-label="Chọn tất cả"
            checked={table.getIsAllPageRowsSelected() || (table.getIsSomePageRowsSelected() && "indeterminate")}
            onCheckedChange={(v) => table.toggleAllPageRowsSelected(!!v)}
          />
        ),
        cell: ({ row }) => <Checkbox aria-label="Chọn dòng" checked={row.getIsSelected()} onCheckedChange={(v) => row.toggleSelected(!!v)} onClick={(e) => e.stopPropagation()} />,
        meta: { className: "w-8" },
      },
      ...columns,
    ];
  }, [columns, selectable]);

  const table = useReactTable({
    data: items,
    columns: allColumns,
    getRowId: (r) => getRowId(r),
    getCoreRowModel: getCoreRowModel(),
    manualPagination: true,
    manualSorting: true,
    manualFiltering: true,
    enableRowSelection: selectable,
    state: { rowSelection: selection },
    onRowSelectionChange: setSelection,
  });

  const selected = table.getSelectedRowModel().rows.map((r) => r.original);
  const clearSelection = () => setSelection({});
  const hasFilters = columns.some((c) => c.meta?.filter);
  const colCount = allColumns.length;

  function toggleSort(key: string) {
    const s = tq.sort;
    tq.setSort(!s || s.key !== key ? { key, desc: false } : !s.desc ? { key, desc: true } : null);
  }

  return (
    <div data-slot="data-table" className="flex h-full min-h-0 flex-col overflow-hidden rounded-lg border bg-card">
      {toolbar && <Toolbar className="shrink-0">
        {onAdd && (
          <ToolbarButton onClick={onAdd}>
            <Plus /> {addLabel}
          </ToolbarButton>
        )}
        {onEdit && (
          <ToolbarButton disabled={selected.length !== 1} onClick={() => onEdit(selected[0])}>
            <Pencil /> Sửa
          </ToolbarButton>
        )}
        {onDelete && (
          <ToolbarButton disabled={selected.length === 0} onClick={() => setConfirming(true)}>
            <Trash2 /> Xóa
          </ToolbarButton>
        )}
        {actions?.({ selected, reload, clearSelection })}
        <ToolbarSeparator />
        <ToolbarButton onClick={() => void reload()}>
          <RefreshCw className={cn(loading && "animate-spin")} /> Nạp
        </ToolbarButton>
        {selected.length > 0 && (
          <span className="ml-auto pr-2 text-xs opacity-80">
            Đã chọn {selected.length}
            <Button variant="link" size="xs" className="text-sidebar-foreground" onClick={clearSelection}>
              Bỏ chọn
            </Button>
          </span>
        )}
      </Toolbar>}
      {/* only this area scrolls; the table's own x-scroll wrapper is disabled so the sticky header works */}
      <div className="min-h-0 flex-1 overflow-auto [&>[data-slot=table-container]]:overflow-visible">
      <Table>
        <TableHeader className="sticky top-0 z-10 bg-card shadow-[inset_0_-1px_0_var(--border)]">
          {table.getHeaderGroups().map((hg) => (
            <TableRow key={hg.id} className="bg-muted/40 hover:bg-muted/40">
              {hg.headers.map((h) => {
                const meta = h.column.columnDef.meta;
                const sortKey = meta?.sort;
                const active = sortKey && tq.sort?.key === sortKey ? tq.sort : null;
                const label = flexRender(h.column.columnDef.header, h.getContext());
                return (
                  <TableHead
                    key={h.id}
                    className={cn("border-r text-xs font-semibold last:border-r-0", meta?.align === "right" && "text-right", meta?.align === "center" && "text-center", meta?.className)}
                    aria-sort={active ? (active.desc ? "descending" : "ascending") : undefined}
                  >
                    {sortKey ? (
                      <Button type="button" variant="ghost" size="xs" className="-mx-1.5 h-6 gap-1 px-1.5 text-xs font-semibold" onClick={() => toggleSort(sortKey)}>
                        {label}
                        {active ? active.desc ? <ArrowDown className="size-3" /> : <ArrowUp className="size-3" /> : <ArrowUpDown className="size-3 opacity-40" />}
                      </Button>
                    ) : (
                      label
                    )}
                  </TableHead>
                );
              })}
            </TableRow>
          ))}
          {hasFilters && (
            <TableRow className="hover:bg-transparent" data-slot="filter-row">
              {table.getLeafHeaders().map((h) => {
                const spec = h.column.columnDef.meta?.filter;
                const header = h.column.columnDef.header;
                return (
                  <TableHead key={h.id} className="h-auto border-r py-1 last:border-r-0">
                    {spec && <FilterCell spec={spec} name={h.column.id} label={typeof header === "string" ? header : h.column.id} get={tq.get} set={tq.setFilters} />}
                  </TableHead>
                );
              })}
            </TableRow>
          )}
        </TableHeader>
        <TableBody>
          {error ? (
            <TableRow>
              <TableCell colSpan={colCount} className="py-6 text-center text-destructive">
                {error}{" "}
                <Button variant="link" size="sm" onClick={() => void reload()}>
                  Thử lại
                </Button>
              </TableCell>
            </TableRow>
          ) : loading && !data ? (
            Array.from({ length: 5 }, (_, i) => (
              <TableRow key={i}>
                <TableCell colSpan={colCount}>
                  <Skeleton className="h-5 w-full" />
                </TableCell>
              </TableRow>
            ))
          ) : items.length === 0 ? (
            <TableRow>
              <TableCell colSpan={colCount} className="py-8 text-center text-muted-foreground">
                {emptyText}
              </TableCell>
            </TableRow>
          ) : (
            table.getRowModel().rows.map((row) => (
              <TableRow
                key={row.id}
                data-state={row.getIsSelected() ? "selected" : activeRowId === row.id ? "selected" : undefined}
                className={cn("even:bg-muted/40", onRowActivate && "cursor-pointer", activeRowId === row.id && "bg-primary/10 even:bg-primary/10", rowClassName?.(row.original))}
                onClick={onRowActivate ? () => onRowActivate(row.original) : undefined}
                tabIndex={onRowActivate ? 0 : undefined}
                onKeyDown={onRowActivate ? (e) => e.key === "Enter" && onRowActivate(row.original) : undefined}
              >
                {row.getVisibleCells().map((cell) => {
                  const meta = cell.column.columnDef.meta;
                  return (
                    <TableCell key={cell.id} className={cn("border-r last:border-r-0", meta?.align === "right" && "text-right tabular-nums", meta?.align === "center" && "text-center", meta?.className)}>
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </TableCell>
                  );
                })}
              </TableRow>
            ))
          )}
        </TableBody>
        {footer && items.length > 0 && (
          <TableFooter className="sticky bottom-0 z-10">
            <TableRow>{footer(items, total)}</TableRow>
          </TableFooter>
        )}
      </Table>
      </div>
      <div className="shrink-0 border-t px-2">
        <Pagination page={tq.page} pageSize={tq.pageSize} total={total} onPage={tq.setPage} onPageSize={tq.setPageSize} />
      </div>
      {onDelete && (
        <ConfirmDialog
          open={confirming}
          onOpenChange={setConfirming}
          destructive
          title={deleteLabel ? deleteLabel(selected) : `Xóa ${selected.length} dòng đã chọn?`}
          description="Thao tác này không hoàn tác được."
          confirmLabel="Xóa"
          onConfirm={async () => {
            setConfirming(false);
            try {
              await onDelete(selected);
            } catch (e) {
              toast.error(e instanceof ApiError ? e.message : "Không xóa được");
            }
            clearSelection();
            await reload();
          }}
        />
      )}
    </div>
  );
}
