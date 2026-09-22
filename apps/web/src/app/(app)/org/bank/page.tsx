"use client";

import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useState } from "react";
import { BankFilters, type BankQuery } from "@/components/bank/BankFilters";
import { BulkBar } from "@/components/bank/BulkBar";
import { QuestionRow } from "@/components/bank/QuestionRow";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/app/EmptyState";
import { PageHeader } from "@/components/app/PageHeader";
import { qs, useApi } from "@/lib/hooks";
import type { Page, ParsedQuestion, Tag, Taxonomy, Topic } from "@/lib/types";

export default function BankPage() {
  const params = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();
  const query: BankQuery = Object.fromEntries(params.entries());
  const setQuery = (v: BankQuery) => router.replace(`${pathname}${qs(v)}`);
  const { data, reload } = useApi<Page<ParsedQuestion>>(`/questions${qs(query)}`);
  const { data: taxonomy } = useApi<Taxonomy>("/taxonomy");
  const { data: topics } = useApi<Topic[]>("/topics");
  const { data: tags } = useApi<Tag[]>("/tags");
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const page = Number(query.page ?? 1);
  const pages = data ? Math.max(1, Math.ceil(data.total / data.page_size)) : 1;
  const toggle = (id: string) =>
    setSelected((s) => {
      const n = new Set(s);
      if (n.has(id)) n.delete(id);
      else n.add(id);
      return n;
    });

  return (
    <>
      <PageHeader
        title="Ngân hàng câu hỏi"
        description={data ? `${data.total} câu` : undefined}
        actions={
          <Link href="/org/bank/new">
            <Button>Thêm câu hỏi</Button>
          </Link>
        }
      />
      {taxonomy && topics && tags && <BankFilters value={query} onChange={setQuery} taxonomy={taxonomy} topics={topics} tags={tags} />}
      <BulkBar ids={[...selected]} topics={topics ?? []} tags={tags ?? []} onDone={reload} onClear={() => setSelected(new Set())} />
      {data && data.items.length > 0 && (
        <label className="mb-2 flex items-center gap-2 text-sm text-muted-foreground">
          <input
            type="checkbox"
            checked={data.items.every((q) => selected.has(q.id))}
            onChange={(e) => setSelected(e.target.checked ? new Set([...selected, ...data.items.map((q) => q.id)]) : new Set())}
          />
          Chọn cả trang
        </label>
      )}
      {data && data.items.length === 0 && <EmptyState>Không có câu hỏi phù hợp.</EmptyState>}
      {data && data.items.length > 0 && (
        <ul className="rounded-xl border border-border bg-card">
          {data.items.map((q) => (
            <QuestionRow key={q.id} q={q} selected={selected.has(q.id)} onToggle={() => toggle(q.id)} />
          ))}
        </ul>
      )}
      {pages > 1 && (
        <div className="mt-4 flex items-center justify-center gap-2 text-sm">
          <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setQuery({ ...query, page: String(page - 1) })}>
            ← Trước
          </Button>
          <span>
            Trang {page}/{pages}
          </span>
          <Button variant="outline" size="sm" disabled={page >= pages} onClick={() => setQuery({ ...query, page: String(page + 1) })}>
            Sau →
          </Button>
        </div>
      )}
    </>
  );
}
