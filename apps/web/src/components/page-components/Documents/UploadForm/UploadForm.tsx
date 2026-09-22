"use client";

import { CheckCircle2, CircleAlert, Copy, Loader2, X } from "lucide-react";
import { FormAlert } from "@/components/app/FormAlert";
import { OptionSelect } from "@/components/app/OptionSelect";
import { DocumentMetaFields } from "@/components/common/DocumentMetaFields/DocumentMetaFields";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { UPLOAD_ACCEPT } from "@/constants/document.constant";
import { type UploadFormOptions, useUploadForm } from "@/hooks/page-hooks/documents/use-upload-form";
import type { DuplicateChoice } from "@/interfaces/document.interface";
import type { Taxonomy } from "@/interfaces/taxonomy.interface";
import { formatDateTime } from "@/lib/datetime";
import { choiceOptions, stateLabel, type UploadRow } from "@/lib/page-libs/documents/upload-rows";
import { cn } from "@/lib/utils";

export interface UploadFormProps extends UploadFormOptions {
  taxonomy: Taxonomy;
  configSlot?: React.ReactNode;
}

/** Upload one or many exam files with the same settings (official-exam-ingestion AC-10).
 *  Fields left on "Tự nhận từ đề" are filled from each file's header. */
export function UploadForm({ taxonomy, configSlot, ...options }: UploadFormProps) {
  const f = useUploadForm(options);
  return (
    <form onSubmit={f.submit} className="space-y-4">
      <div
        onDragOver={(e) => (e.preventDefault(), f.setDrag(true))}
        onDragLeave={() => f.setDrag(false)}
        onDrop={(e) => {
          e.preventDefault();
          f.setDrag(false);
          f.add(e.dataTransfer.files);
        }}
        className={cn("rounded-xl border-2 border-dashed p-6 text-center text-sm", f.drag ? "border-primary bg-primary/10" : "border-input")}
      >
        <p className="mb-2 text-muted-foreground">Kéo thả một hoặc nhiều file đề vào đây (.docx, .pdf, ảnh chụp)</p>
        <Input ref={f.input} data-testid="file" type="file" multiple accept={UPLOAD_ACCEPT} aria-label="Chọn file đề" className="mx-auto max-w-sm" onChange={(e) => f.add(e.target.files)} />
        {f.fields.file && <p className="mt-2 text-xs text-destructive">{f.fields.file}</p>}
      </div>
      {f.rows.length > 0 && (
        <ul className="divide-y rounded-lg border text-sm" aria-label="File đã chọn">
          {f.rows.map((r, i) => (
            <li key={`${r.file.name}-${i}`} className="grid gap-1 px-3 py-1.5" data-testid={`upload-row-${i}`}>
              <div className="flex items-center gap-2">
                <FileState row={r} />
                <span className="min-w-0 flex-1 truncate" title={r.file.name}>
                  {r.file.name}
                </span>
                <span className={cn("shrink-0 text-xs", r.state === "error" ? "text-destructive" : "text-muted-foreground")}>{stateLabel(r)}</span>
                {(r.state === "waiting" || r.state === "error") && !f.busy && (
                  <Button type="button" variant="ghost" size="icon-xs" aria-label={`Bỏ ${r.file.name}`} onClick={() => f.remove(i)}>
                    <X />
                  </Button>
                )}
              </div>
              {r.conflict && r.state === "waiting" && (
                <div className="flex flex-wrap items-center gap-2 pl-6 text-xs text-amber-700 dark:text-amber-400">
                  <span className="min-w-0 flex-1">
                    {r.conflict.same_file
                      ? `Đã có file giống hệt: “${r.conflict.same_file.filename}” (${r.conflict.same_file.question_count} câu, ${formatDateTime(r.conflict.same_file.created_at)})`
                      : `Trùng tên với ${r.conflict.same_name.length} đề đã tải, mới nhất lúc ${formatDateTime(r.conflict.same_name[0].created_at)}`}
                  </span>
                  <OptionSelect
                    size="sm"
                    className="h-7 w-52"
                    aria-label={`Cách xử lý ${r.file.name}`}
                    value={r.choice ?? "skip"}
                    onValueChange={(v) => f.setChoice(i, v as DuplicateChoice)}
                    options={choiceOptions(r.conflict)}
                  />
                </div>
              )}
            </li>
          ))}
        </ul>
      )}
      {f.conflicts > 1 && (
        <div className="flex flex-wrap items-center gap-2 text-sm">
          <span className="text-muted-foreground">{f.conflicts} file trùng:</span>
          <Button type="button" size="xs" variant="outline" onClick={() => f.setAll("skip")}>
            Bỏ qua tất cả
          </Button>
          <Button type="button" size="xs" variant="outline" onClick={() => f.setAll("replace")}>
            Ghi đè / tách lại tất cả
          </Button>
        </div>
      )}
      <DocumentMetaFields value={f.meta} onChange={f.setMeta} taxonomy={taxonomy} years={f.years} errors={f.fields} emptyLabel="Tự nhận từ đề" />
      {configSlot}
      {f.error && !Object.keys(f.fields).length && <FormAlert kind="warning">{f.error}</FormAlert>}
      <div className="flex justify-end">
        <Button type="submit" disabled={f.busy || f.checking}>
          {f.checking ? "Đang kiểm tra file trùng…" : f.busy ? "Đang tải lên…" : f.waiting > 1 ? `Tải lên ${f.waiting} file và tách câu` : "Tải lên và tách câu"}
        </Button>
      </div>
    </form>
  );
}

function FileState({ row }: { row: UploadRow }) {
  const cls = "size-4 shrink-0";
  if (row.state === "sending" || row.state === "checking") return <Loader2 className={cn(cls, "animate-spin text-muted-foreground")} />;
  if (row.state === "queued" || row.state === "replaced") return <CheckCircle2 className={cn(cls, "text-emerald-600")} />;
  if (row.state === "duplicate" || row.state === "skipped") return <Copy className={cn(cls, "text-amber-600")} />;
  if (row.state === "error") return <CircleAlert className={cn(cls, "text-destructive")} />;
  return <span className={cn(cls, "rounded-full border")} />;
}
