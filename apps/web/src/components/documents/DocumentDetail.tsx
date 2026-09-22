"use client";

import { BackLink } from "@/components/app/BackLink";
// Document review page body (moved out of app/(app)/org/documents/[id]/page.tsx so it can be tested).

import { FilePlus2 } from "lucide-react";
import { Checkbox } from "@/components/ui/checkbox";
import { useRouter, useSearchParams } from "next/navigation";
import { toast } from "sonner";
import { useEffect, useState } from "react";
import { DocumentInfo } from "@/components/documents/DocumentInfo";
import { metaLabel, StatusBadge } from "@/components/documents/DocumentList";
import { metaChips, ParsedQuestionCard } from "@/components/documents/ParsedQuestion";
import { ProcessingConfigFields } from "@/components/documents/ProcessingConfig";
import { FormAlert } from "@/components/app/FormAlert";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { EmptyState } from "@/components/app/EmptyState";
import { FormDialog } from "@/components/app/FormDialog";
import { PageHeader } from "@/components/app/PageHeader";
import { api, ApiError } from "@/lib/api";
import { useApi } from "@/lib/hooks";
import type { AiModel, Page, ParsedQuestion, ProcessingConfig, SourceDocument, Taxonomy } from "@/lib/types";

export function DocumentDetail({ id }: { id: string }) {
  const dup = useSearchParams().get("dup");
  const router = useRouter();
  const [making, setMaking] = useState(false);
  const { data: doc, reload } = useApi<SourceDocument>(`/documents/${id}`);
  const { data: taxonomy } = useApi<Taxonomy>("/taxonomy");
  const parsed = doc?.status === "parsed";
  const { data: questions, reload: reloadQuestions } = useApi<ParsedQuestion[]>(parsed ? `/documents/${id}/questions` : null);
  const [onlyIssues, setOnlyIssues] = useState(false);
  const [reparse, setReparse] = useState<ProcessingConfig | null>(null);
  const [reparseError, setReparseError] = useState<string | null>(null);
  const { data: modelsPage } = useApi<Page<AiModel>>(reparse ? "/ai-models?enabled=true&page_size=all" : null);
  const models = modelsPage?.items;
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
      <BackLink href="/org/documents">Đề đã tải lên</BackLink>
      <PageHeader
        title={doc.filename}
        description={metaLabel(doc, taxonomy)}
        actions={
          <>
            <StatusBadge doc={doc} />
            {!busy && (
              <Button variant="outline" size="sm" onClick={() => setReparse(doc.processing_config)}>
                Tách lại
              </Button>
            )}
            {parsed && (
              <Button
                size="sm"
                disabled={making}
                onClick={async () => {
                  setMaking(true);
                  try {
                    const r = await api<{ exam_id: string; added: number; skipped: number }>(`/documents/${doc.id}/exam`, { body: {} });
                    toast.success(`Đã tạo đề thi với ${r.added} câu` + (r.skipped ? ` — bỏ qua ${r.skipped} câu chưa duyệt` : ""));
                    router.push(`/org/exams/${r.exam_id}`);
                  } catch (e) {
                    toast.error(e instanceof ApiError ? e.message : "Không tạo được đề");
                  } finally {
                    setMaking(false);
                  }
                }}
              >
                <FilePlus2 /> Tạo đề từ tài liệu
              </Button>
            )}
          </>
        }
      />
      <FormDialog open={!!reparse} title="Tách lại với cấu hình khác" wide onOpenChange={(o) => !o && setReparse(null)}>
        {reparse && (
          <div className="space-y-4">
            <FormAlert kind="warning">Các câu chưa duyệt của đề này sẽ được thay bằng kết quả mới; câu đã duyệt được giữ nguyên.</FormAlert>
            <ProcessingConfigFields value={reparse} onChange={setReparse} models={models ?? []} />
            {reparseError && <FormAlert>{reparseError}</FormAlert>}
            <div className="flex justify-end">
              <Button
               
                onClick={async () => {
                  try {
                    await api(`/documents/${doc.id}/reparse`, { body: { config: reparse } });
                    setReparse(null);
                    void reload();
                  } catch (e) {
                    setReparseError(e instanceof ApiError ? e.message : "Có lỗi xảy ra");
                  }
                }}
              >
                Tách lại
              </Button>
            </div>
          </div>
        )}
      </FormDialog>
      {taxonomy && !busy && <DocumentInfo doc={doc} taxonomy={taxonomy} onSaved={() => (void reload(), void reloadQuestions())} />}
      {dup && <div className="mb-4"><FormAlert kind="info">File này đã được tải lên trước đó — đây là bản đã có.</FormAlert></div>}
      {busy && <FormAlert kind="warning">Đang tách câu hỏi… trang sẽ tự cập nhật.</FormAlert>}
      {doc.status === "failed" && <FormAlert>{doc.error}</FormAlert>}
      {warnings.length > 0 && (
        <div className="mb-4">
          <FormAlert kind="warning">{warnings.join(" · ")}</FormAlert>
        </div>
      )}
      {parsed && questions && (
        <>
          <div className="mb-4 flex items-center gap-4 text-sm text-muted-foreground">
            <span>
              {questions.length} câu · {low} câu cần xem
            </span>
            <Label className="font-normal">
              <Checkbox checked={onlyIssues} onCheckedChange={(v) => setOnlyIssues(v === true)} /> Chỉ hiện câu cần xem
            </Label>
            <Button variant="link" asChild className="ml-auto h-auto p-0">
              <a href={`/api/documents/${doc.id}/file`}>Tải file gốc</a>
            </Button>
          </div>
          {shown.length === 0 && <EmptyState>Không có câu nào.</EmptyState>}
          <div className="space-y-4">
            {shown.map((q) => (
              <ParsedQuestionCard
                key={q.id}
                q={q}
                threshold={threshold}
                meta={metaChips(q, taxonomy?.subjects.find((s) => s.id === q.subject_id)?.name)}
              />
            ))}
          </div>
        </>
      )}
    </>
  );
}
