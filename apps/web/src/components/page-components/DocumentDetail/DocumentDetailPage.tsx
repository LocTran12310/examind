"use client";

import { FilePlus2 } from "lucide-react";
import { BackLink } from "@/components/common/BackLink/BackLink";
import { EmptyState } from "@/components/common/EmptyState/EmptyState";
import { FormAlert } from "@/components/common/FormAlert/FormAlert";
import { FormDialog } from "@/components/common/FormDialog/FormDialog";
import { PageHeader } from "@/components/common/PageHeader/PageHeader";
import { DocumentStatusBadge } from "@/components/common/DocumentStatusBadge/DocumentStatusBadge";
import { ProcessingConfigFields } from "@/components/common/ProcessingConfig/ProcessingConfig";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { useDocumentDetailPage } from "@/hooks/page-hooks/document-detail/use-document-detail-page";
import { metaLabel } from "@/lib/common/document-label";
import { DocumentInfo } from "./DocumentInfo/DocumentInfo";
import { metaChips, ParsedQuestionCard } from "./ParsedQuestionCard/ParsedQuestionCard";

export function DocumentDetailPage({ id }: { id: string }) {
  const p = useDocumentDetailPage(id);
  const { doc, taxonomy } = p;
  if (!doc) return null;
  return (
    <>
      <BackLink href="/org/documents">Đề đã tải lên</BackLink>
      <PageHeader
        title={doc.filename}
        description={metaLabel(doc, taxonomy)}
        actions={
          <>
            <DocumentStatusBadge doc={doc} />
            {!p.busy && (
              <Button variant="outline" size="sm" onClick={p.openReparse}>
                Tách lại
              </Button>
            )}
            {p.parsed && (
              <Button size="sm" disabled={p.making} onClick={p.createExam}>
                <FilePlus2 /> Tạo đề từ tài liệu
              </Button>
            )}
          </>
        }
      />
      <FormDialog open={!!p.reparseConfig} title="Tách lại với cấu hình khác" wide onOpenChange={(o) => !o && p.setReparseConfig(null)}>
        {p.reparseConfig && (
          <div className="space-y-4">
            <FormAlert kind="warning">Các câu chưa duyệt của đề này sẽ được thay bằng kết quả mới; câu đã duyệt được giữ nguyên.</FormAlert>
            <ProcessingConfigFields value={p.reparseConfig} onChange={p.setReparseConfig} models={p.models} />
            {p.reparseError && <FormAlert>{p.reparseError}</FormAlert>}
            <div className="flex justify-end">
              <Button onClick={p.submitReparse}>Tách lại</Button>
            </div>
          </div>
        )}
      </FormDialog>
      {taxonomy && !p.busy && <DocumentInfo doc={doc} taxonomy={taxonomy} />}
      {p.duplicate && <div className="mb-4"><FormAlert kind="info">File này đã được tải lên trước đó — đây là bản đã có.</FormAlert></div>}
      {p.busy && <FormAlert kind="warning">Đang tách câu hỏi… trang sẽ tự cập nhật.</FormAlert>}
      {doc.status === "failed" && <FormAlert>{doc.error}</FormAlert>}
      {p.warnings.length > 0 && (
        <div className="mb-4">
          <FormAlert kind="warning">{p.warnings.join(" · ")}</FormAlert>
        </div>
      )}
      {p.parsed && p.questions && (
        <>
          <div className="mb-4 flex items-center gap-4 text-sm text-muted-foreground">
            <span>
              {p.questions.length} câu · {p.low} câu cần xem
            </span>
            <Label className="font-normal">
              <Checkbox checked={p.onlyIssues} onCheckedChange={(v) => p.setOnlyIssues(v === true)} /> Chỉ hiện câu cần xem
            </Label>
            <Button variant="link" asChild className="ml-auto h-auto p-0">
              <a href={p.fileUrl}>Tải file gốc</a>
            </Button>
          </div>
          {p.shown.length === 0 && <EmptyState>Không có câu nào.</EmptyState>}
          <div className="space-y-4">
            {p.shown.map((q) => (
              <ParsedQuestionCard key={q.id} q={q} threshold={p.threshold} meta={metaChips(q, taxonomy?.subjects.find((s) => s.id === q.subject_id)?.name)} />
            ))}
          </div>
        </>
      )}
    </>
  );
}
