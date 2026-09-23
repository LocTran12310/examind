"use client";

import { RefreshCw } from "lucide-react";
import { EmptyState } from "@/components/common/EmptyState/EmptyState";
import { FormDialog } from "@/components/common/FormDialog/FormDialog";
import { ListLayout } from "@/components/common/ListLayout/ListLayout";
import { OptionSelect } from "@/components/common/OptionSelect/OptionSelect";
import { PageHeader } from "@/components/common/PageHeader/PageHeader";
import { Pagination } from "@/components/common/DataTable/Pagination";
import { Toolbar, ToolbarButton, ToolbarSeparator } from "@/components/common/DataTable/Toolbar";
import { TopicPicker } from "@/components/common/TopicPicker/TopicPicker";
import { BulkTopicBar } from "@/components/page-components/TaggingQueue/BulkTopicBar/BulkTopicBar";
import { UntaggedRow } from "@/components/page-components/TaggingQueue/UntaggedRow/UntaggedRow";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { BULK, useTaggingQueue } from "@/hooks/page-hooks/tagging-queue/use-tagging-queue";
import { cn } from "@/lib/utils";

export function TaggingQueuePage() {
  const p = useTaggingQueue();
  return (
    <ListLayout
      header={<PageHeader title="Chưa gắn chuyên đề" description={p.total === undefined ? "Những câu chưa có chuyên đề, mới nhất trước" : `Còn ${p.total.toLocaleString("vi-VN")} câu chưa gắn chuyên đề`} />}
    >
      <>
        <div className="flex h-full min-h-0 flex-col overflow-hidden rounded-lg border bg-card">
          <Toolbar className="shrink-0">
            <BulkTopicBar count={p.selected.size} suggestable={p.suggestable} mixed={p.mixedSubjects} onApplySuggestions={p.applySuggestions} onPick={() => p.setPicking(BULK)} onClear={p.clearSelection} />
            <ToolbarSeparator />
            <ToolbarButton onClick={p.reload}>
              <RefreshCw className={cn(p.loading && "animate-spin")} /> Nạp
            </ToolbarButton>
            {p.modelPending && <span className="pl-2 text-xs opacity-80">Đang hỏi AI cho các câu chưa có gợi ý…</span>}
            <span className="ml-auto pr-2 text-xs opacity-80">
              <span className="font-mono">1</span> / <span className="font-mono">2</span> / <span className="font-mono">3</span> chọn gợi ý · <span className="font-mono">↑</span> <span className="font-mono">↓</span> chuyển câu
            </span>
          </Toolbar>
          <div className="flex flex-wrap items-center gap-2 border-b px-3 py-2">
            <OptionSelect
              size="sm"
              aria-label="Môn"
              className="w-48"
              value={p.subjectId}
              onValueChange={(v) => p.setFilter("subject_id", v)}
              options={p.subjectOptions}
              emptyLabel="Mọi môn"
            />
            <OptionSelect
              size="sm"
              aria-label="Đề gốc"
              className="w-72"
              value={p.documentId}
              onValueChange={(v) => p.setFilter("document_id", v)}
              options={p.documentOptions}
              emptyLabel="Mọi đề"
              onEndReached={p.loadMoreDocuments}
              loadingMore={p.loadingDocuments}
            />
            {p.rows.length > 0 && (
              <Label className="ml-auto font-normal text-muted-foreground">
                <Checkbox checked={p.allOnPage} onCheckedChange={(v) => p.selectPage(!!v)} aria-label="Chọn cả trang" />
                Chọn cả trang
              </Label>
            )}
          </div>
          <div className="min-h-0 flex-1 overflow-auto">
            {!p.loaded && p.loading && (
              <div className="grid gap-2 p-3">
                {Array.from({ length: 4 }, (_, i) => (
                  <Skeleton key={i} className="h-24" />
                ))}
              </div>
            )}
            {p.loaded && p.rows.length === 0 && (
              <div className="p-3">
                <EmptyState>Không còn câu nào chưa gắn chuyên đề. 🎉</EmptyState>
              </div>
            )}
            {p.rows.length > 0 && (
              <ul>
                {p.rows.map((row, i) => (
                  <UntaggedRow
                    key={row.q.id}
                    row={row}
                    focused={i === p.at}
                    selected={p.selected.has(row.q.id)}
                    onToggle={() => p.toggle(row.q.id)}
                    onFocus={() => p.setFocus(i)}
                    onApply={(s) => p.applySuggestion(row.q.id, s)}
                    onOther={() => p.setPicking(row.q.id)}
                  />
                ))}
              </ul>
            )}
          </div>
          <div className="shrink-0 border-t px-2">
            <Pagination page={p.tq.page} pageSize={p.tq.pageSize} total={p.total ?? 0} onPage={p.tq.setPage} onPageSize={p.tq.setPageSize} />
          </div>
        </div>
        <FormDialog open={!!p.picking} title={p.pickerTitle} onOpenChange={(o) => !o && p.setPicking(null)}>
          <TopicPicker topics={p.pickerTopics} counts={p.pickerCounts} initial={p.pickerInitial} onPick={p.pickTopic} onClose={() => p.setPicking(null)} />
        </FormDialog>
      </>
    </ListLayout>
  );
}
