"use client";

import { Label } from "@/components/ui/label";
import { ListLayout } from "@/components/app/ListLayout";
import { Plus, RefreshCw } from "lucide-react";
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { EmptyState } from "@/components/app/EmptyState";
import { PageHeader } from "@/components/app/PageHeader";
import { useMeMaybe } from "@/app/(app)/AppShell";
import { BankFilters } from "@/components/bank/BankFilters";
import { SUBJECT_SCOPED } from "@/components/bank/filters";
import { NO_SUBJECT, SubjectTabs } from "@/components/bank/SubjectTabs";
import { BulkActions } from "@/components/bank/BulkBar";
import { QuestionRow } from "@/components/bank/QuestionRow";
import { Pagination } from "@/components/common/DataTable/Pagination";
import { Toolbar, ToolbarButton, ToolbarSeparator } from "@/components/common/DataTable/Toolbar";
import { useTableQuery } from "@/hooks/common/use-table-query";
import { Checkbox } from "@/components/ui/checkbox";
import { Skeleton } from "@/components/ui/skeleton";
import { useApi } from "@/lib/hooks";
import type { BankFacets, Page, ParsedQuestion, Tag, Taxonomy, Topic } from "@/lib/types";
import { cn } from "@/lib/utils";
// eslint-disable-next-line no-restricted-imports -- screen moves to a page hook in its own slice
import { useTagOptionsQuery } from "@/hooks/react-query/use-query-tag";

const subjectKey = (orgId: string) => `examind.bank.subject.${orgId}`;
function storedSubject(orgId?: string): string | null {
  try {
    return orgId ? localStorage.getItem(subjectKey(orgId)) : null;
  } catch {
    return null;
  }
}

export default function BankPage() {
  const me = useMeMaybe();
  const tq = useTableQuery();
  const subject = tq.apiParams.get("subject_id") ?? "";
  const query = tq.apiParams.toString();
  const { data: taxonomy } = useApi<Taxonomy>("/taxonomy");
  // counts per subject/topic/tag… for the tabs and the sheet; also picks the default subject
  const { data: facets } = useApi<BankFacets>(`/questions/facets?${query}`);
  const { data, reload, loading } = useApi<Page<ParsedQuestion>>(subject ? `/questions?${query}` : null);
  const scoped = subject && subject !== NO_SUBJECT ? subject : null;
  const { data: topics } = useApi<Topic[]>(scoped ? `/topics?subject_id=${scoped}` : null);
  const { data: tags } = useTagOptionsQuery(scoped || "shared", !!(scoped || subject));
  const [selected, setSelected] = useState<Set<string>>(new Set());
  useEffect(() => setSelected(new Set()), [query]);

  // no subject in the URL: the last one used here, else the one with most questions (A-01, A-03)
  useEffect(() => {
    if (subject || !taxonomy || !facets) return;
    const counts = facets.subjects;
    const last = storedSubject(me?.org.id);
    const best = [...taxonomy.subjects].sort((a, b) => (counts[b.id] ?? 0) - (counts[a.id] ?? 0))[0]?.id;
    const pick = last && (taxonomy.subjects.some((x) => x.id === last) || last === NO_SUBJECT) ? last : best;
    if (pick) tq.setFilters({ subject_id: pick });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [subject, taxonomy, facets]);

  function chooseSubject(id: string) {
    try {
      if (me) localStorage.setItem(subjectKey(me.org.id), id);
    } catch {}
    tq.setFilters({ subject_id: id, ...Object.fromEntries(SUBJECT_SCOPED.map((k) => [k, null])) });
  }

  const filters = useMemo(() => Object.fromEntries([...tq.apiParams.entries()].filter(([k]) => k !== "page" && k !== "page_size" && k !== "subject_id")), [tq.apiParams]);
  const subjectName = taxonomy?.subjects.find((x) => x.id === subject)?.name ?? (subject === NO_SUBJECT ? "Chưa phân môn" : undefined);
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
          <BulkActions ids={[...selected]} topics={topics ?? []} tags={tags ?? []} onDone={() => void reload()} onClear={() => setSelected(new Set())} />
          <ToolbarSeparator />
          <ToolbarButton onClick={() => void reload()}>
            <RefreshCw className={cn(loading && "animate-spin")} /> Nạp
          </ToolbarButton>
          {selected.size > 0 && <span className="ml-auto pr-2 text-xs opacity-80">Đã chọn {selected.size}</span>}
        </Toolbar>
        <div className="min-h-0 flex-1 overflow-auto">
        {taxonomy && (
          <div className="border-b px-3 pt-3">
            <SubjectTabs subjects={taxonomy.subjects} counts={facets?.subjects} value={subject} onChange={chooseSubject} />
          </div>
        )}
        {taxonomy && tags && (topics || !scoped) && (
          <BankFilters value={filters} onChange={tq.setFilters} taxonomy={taxonomy} topics={topics ?? []} tags={tags} facets={facets} subjectName={subjectName} />
        )}
        {items.length > 0 && (
          <Label className="border-b px-3 py-2 font-normal text-muted-foreground">
            <Checkbox checked={allOnPage} onCheckedChange={(v) => setSelected(v ? new Set([...selected, ...items.map((q) => q.id)]) : new Set())} aria-label="Chọn cả trang" />
            Chọn cả trang
          </Label>
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
