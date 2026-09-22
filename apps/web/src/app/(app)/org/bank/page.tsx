"use client";

import { ListLayout } from "@/components/app/ListLayout";
import { Plus, RefreshCw } from "lucide-react";
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { EmptyState } from "@/components/app/EmptyState";
import { PageHeader } from "@/components/app/PageHeader";
import { BankFilters } from "@/components/bank/BankFilters";
import { BulkActions } from "@/components/bank/BulkBar";
import { QuestionRow } from "@/components/bank/QuestionRow";
import { Pagination } from "@/components/data-table/Pagination";
import { Toolbar, ToolbarButton, ToolbarSeparator } from "@/components/data-table/Toolbar";
import { useTableQuery } from "@/components/data-table/useTableQuery";
import { Checkbox } from "@/components/ui/checkbox";
import { Skeleton } from "@/components/ui/skeleton";
import { useApi } from "@/lib/hooks";
import type { Page, ParsedQuestion, Tag, Taxonomy, Topic } from "@/lib/types";
import { cn } from "@/lib/utils";

export default function BankPage() {
  const tq = useTableQuery();
  const query = tq.apiParams.toString();
  const { data, reload, loading } = useApi<Page<ParsedQuestion>>(`/questions?${query}`);
  const { data: taxonomy } = useApi<Taxonomy>("/taxonomy");
  const { data: topics } = useApi<Topic[]>("/topics");
  const { data: tagsPage } = useApi<Page<Tag>>("/tags?page_size=all");
  const tags = tagsPage?.items;
  const [selected, setSelected] = useState<Set<string>>(new Set());
  useEffect(() => setSelected(new Set()), [query]);
  const filters = useMemo(() => Object.fromEntries([...tq.apiParams.entries()].filter(([k]) => k !== "page" && k !== "page_size")), [tq.apiParams]);
  const items = data?.items ?? [];
  const allOnPage = items.length > 0 && items.every((q) => selected.has(q.id));
  const toggle = (id: string) =>
    setSelected((s) => {
      const n = new Set(s);
      if (n.has(id)) n.delete(id);
      else n.add(id);
      return n;
    });

  return (
    <>
      <ListLayout header={<PageHeader title="Ngân hàng câu hỏi" description={data ? `${data.total.toLocaleString("vi-VN")} câu` : undefined} />}>
      <div className="flex h-full min-h-0 flex-col overflow-hidden rounded-lg border bg-card">
        <Toolbar className="shrink-0">
          <ToolbarButton asChild>
            <Link href="/org/bank/new">
              <Plus /> Thêm câu hỏi
            </Link>
          </ToolbarButton>
          <ToolbarSeparator />
          <BulkActions ids={[...selected]} topics={topics ?? []} tags={tags ?? []} onDone={reload} onClear={() => setSelected(new Set())} />
          <ToolbarSeparator />
          <ToolbarButton onClick={() => void reload()}>
            <RefreshCw className={cn(loading && "animate-spin")} /> Nạp
          </ToolbarButton>
          {selected.size > 0 && <span className="ml-auto pr-2 text-xs opacity-80">Đã chọn {selected.size}</span>}
        </Toolbar>
        <div className="min-h-0 flex-1 overflow-auto">
        {taxonomy && topics && tags && <BankFilters value={filters} onChange={tq.setFilters} taxonomy={taxonomy} topics={topics} tags={tags} />}
        {items.length > 0 && (
          <label className="flex items-center gap-2 border-b px-3 py-2 text-sm text-muted-foreground">
            <Checkbox checked={allOnPage} onCheckedChange={(v) => setSelected(v ? new Set([...selected, ...items.map((q) => q.id)]) : new Set())} aria-label="Chọn cả trang" />
            Chọn cả trang
          </label>
        )}
        {!data && loading && (
          <div className="grid gap-2 p-3">
            {Array.from({ length: 4 }, (_, i) => (
              <Skeleton key={i} className="h-14" />
            ))}
          </div>
        )}
        {data && items.length === 0 && (
          <div className="p-3">
            <EmptyState>Không có câu hỏi phù hợp.</EmptyState>
          </div>
        )}
        {items.length > 0 && (
          <ul>
            {items.map((q) => (
              <QuestionRow key={q.id} q={q} selected={selected.has(q.id)} onToggle={() => toggle(q.id)} />
            ))}
          </ul>
        )}
        </div>
        <div className="shrink-0 border-t px-2">
          <Pagination page={tq.page} pageSize={tq.pageSize} total={data?.total ?? 0} onPage={tq.setPage} onPageSize={tq.setPageSize} />
        </div>
      </div>
      </ListLayout>
    </>
  );
}
