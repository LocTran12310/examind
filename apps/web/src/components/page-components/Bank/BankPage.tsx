"use client";

import { Plus, RefreshCw } from "lucide-react";
import Link from "next/link";
import { EmptyState } from "@/components/app/EmptyState";
import { ListLayout } from "@/components/app/ListLayout";
import { PageHeader } from "@/components/app/PageHeader";
import { Pagination } from "@/components/common/DataTable/Pagination";
import { Toolbar, ToolbarButton, ToolbarSeparator } from "@/components/common/DataTable/Toolbar";
import { BankFilters } from "@/components/page-components/Bank/BankFilters/BankFilters";
import { BulkActions } from "@/components/page-components/Bank/BulkBar/BulkBar";
import { QuestionRow } from "@/components/page-components/Bank/QuestionRow/QuestionRow";
import { SubjectTabs } from "@/components/page-components/Bank/SubjectTabs/SubjectTabs";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { useBankPage } from "@/hooks/page-hooks/bank/use-bank-page";
import { cn } from "@/lib/utils";

export function BankPage() {
  const p = useBankPage();
  return (
    <ListLayout header={<PageHeader title="Ngân hàng câu hỏi" description={p.total !== undefined ? `${p.total.toLocaleString("vi-VN")} câu` : undefined} />}>
      <div className="flex h-full min-h-0 flex-col overflow-hidden rounded-lg border bg-card">
        <Toolbar className="shrink-0">
          <ToolbarButton asChild>
            <Link href="/org/bank/new">
              <Plus /> Thêm câu hỏi
            </Link>
          </ToolbarButton>
          <ToolbarSeparator />
          <BulkActions ids={[...p.selected]} topics={p.topics ?? []} tags={p.tags ?? []} onClear={p.clearSelection} />
          <ToolbarSeparator />
          <ToolbarButton onClick={p.reload}>
            <RefreshCw className={cn(p.loading && "animate-spin")} /> Nạp
          </ToolbarButton>
          {p.selected.size > 0 && <span className="ml-auto pr-2 text-xs opacity-80">Đã chọn {p.selected.size}</span>}
        </Toolbar>
        <div className="min-h-0 flex-1 overflow-auto">
          {p.taxonomy && (
            <div className="border-b px-3 pt-3">
              <SubjectTabs subjects={p.taxonomy.subjects} counts={p.facets?.subjects} value={p.subject} onChange={p.chooseSubject} />
            </div>
          )}
          {p.taxonomy && p.tags && (p.topics || !p.scoped) && (
            <BankFilters value={p.filters} onChange={p.tq.setFilters} taxonomy={p.taxonomy} topics={p.topics ?? []} tags={p.tags} facets={p.facets} subjectName={p.subjectName} />
          )}
          {p.items.length > 0 && (
            <Label className="border-b px-3 py-2 font-normal text-muted-foreground">
              <Checkbox checked={p.allOnPage} onCheckedChange={(v) => p.selectPage(!!v)} aria-label="Chọn cả trang" />
              Chọn cả trang
            </Label>
          )}
          {!p.loaded && p.loading && (
            <div className="grid gap-2 p-3">
              {Array.from({ length: 4 }, (_, i) => (
                <Skeleton key={i} className="h-14" />
              ))}
            </div>
          )}
          {p.loaded && p.items.length === 0 && (
            <div className="p-3">
              <EmptyState>Không có câu hỏi phù hợp.</EmptyState>
            </div>
          )}
          {p.items.length > 0 && (
            <ul>
              {p.items.map((q) => (
                <QuestionRow key={q.id} q={q} selected={p.selected.has(q.id)} onToggle={() => p.toggle(q.id)} />
              ))}
            </ul>
          )}
        </div>
        <div className="shrink-0 border-t px-2">
          <Pagination page={p.tq.page} pageSize={p.tq.pageSize} total={p.total ?? 0} onPage={p.tq.setPage} onPageSize={p.tq.setPageSize} />
        </div>
      </div>
    </ListLayout>
  );
}
