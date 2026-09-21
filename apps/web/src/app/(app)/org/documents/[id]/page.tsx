"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { use, useEffect, useState } from "react";
import { metaLabel, StatusBadge } from "@/components/documents/DocumentList";
import { ParsedQuestionCard } from "@/components/documents/ParsedQuestion";
import { Alert, Empty, PageHeader } from "@/components/ui";
import { useApi } from "@/lib/hooks";
import type { ParsedQuestion, SourceDocument, Taxonomy } from "@/lib/types";

export default function DocumentPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const dup = useSearchParams().get("dup");
  const { data: doc, reload } = useApi<SourceDocument>(`/documents/${id}`);
  const { data: taxonomy } = useApi<Taxonomy>("/taxonomy");
  const parsed = doc?.status === "parsed";
  const { data: questions, reload: reloadQuestions } = useApi<ParsedQuestion[]>(parsed ? `/documents/${id}/questions` : null);
  const [onlyIssues, setOnlyIssues] = useState(false);
  const busy = doc && (doc.status === "queued" || doc.status === "processing");

  useEffect(() => {
    if (!busy) return;
    const t = setInterval(reload, 2000);
    return () => clearInterval(t);
  }, [busy, reload]);
  useEffect(() => {
    if (parsed) void reloadQuestions();
  }, [parsed, reloadQuestions]);

  if (!doc) return null;
  const threshold = doc.processing_config?.threshold ?? 0.85;
  const warnings = doc.log.find((l) => l.step === "warnings")?.items ?? [];
  const shown = (questions ?? []).filter((q) => !onlyIssues || (q.confidence ?? 0) < threshold);
  const low = (questions ?? []).filter((q) => (q.confidence ?? 0) < threshold).length;

  return (
    <>
      <Link href="/org/documents" className="text-sm text-gray-500 hover:underline">
        ← Đề đã tải lên
      </Link>
      <PageHeader title={doc.filename} subtitle={metaLabel(doc, taxonomy)} actions={<StatusBadge doc={doc} />} />
      {dup && <div className="mb-4"><Alert tone="blue">File này đã được tải lên trước đó — đây là bản đã có.</Alert></div>}
      {busy && <Alert tone="amber">Đang tách câu hỏi… trang sẽ tự cập nhật.</Alert>}
      {doc.status === "failed" && <Alert>{doc.error}</Alert>}
      {warnings.length > 0 && (
        <div className="mb-4">
          <Alert tone="amber">{warnings.join(" · ")}</Alert>
        </div>
      )}
      {parsed && questions && (
        <>
          <div className="mb-4 flex items-center gap-4 text-sm text-gray-600">
            <span>
              {questions.length} câu · {low} câu cần xem
            </span>
            <label className="flex items-center gap-2">
              <input type="checkbox" checked={onlyIssues} onChange={(e) => setOnlyIssues(e.target.checked)} /> Chỉ hiện câu cần xem
            </label>
            <a className="ml-auto text-brand-700 hover:underline" href={`/api/documents/${doc.id}/file`}>
              Tải file gốc
            </a>
          </div>
          {shown.length === 0 && <Empty>Không có câu nào.</Empty>}
          <div className="space-y-4">
            {shown.map((q) => (
              <ParsedQuestionCard key={q.id} q={q} threshold={threshold} />
            ))}
          </div>
        </>
      )}
    </>
  );
}
