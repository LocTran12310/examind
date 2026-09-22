"use client";

import { Pencil, ScanText } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import { FormAlert } from "@/components/app/FormAlert";
import { FormDialog } from "@/components/app/FormDialog";
import { useYear } from "@/components/app/YearContext";
import { Button } from "@/components/ui/button";
import { api, ApiError } from "@/lib/api";
import type { DetectedHeader, DocumentMeta, SourceDocument, Taxonomy } from "@/lib/types";
import { DocumentMetaFields } from "./DocumentMetaFields";

export function detectedLabel(d?: DetectedHeader): string {
  if (!d) return "";
  const kind = d.exam_kind ? `${d.exam_kind}${d.attempt ? ` lần ${d.attempt}` : ""}` : null;
  return [d.issuer, d.school_year, d.subject_name, d.grade ? `Lớp ${d.grade}` : null, kind, d.duration ? `${d.duration} phút` : null].filter(Boolean).join(" · ");
}

/** "Nhận từ tiêu đề đề thi: …" + edit the document's subject / grade / đợt / năm học / nguồn. */
export function DocumentInfo({ doc, taxonomy, onSaved }: { doc: SourceDocument; taxonomy: Taxonomy; onSaved: () => void }) {
  const [editing, setEditing] = useState<DocumentMeta | null>(null);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [error, setError] = useState<string | null>(null);
  const { years } = useYear();
  const detected = detectedLabel(doc.meta.detected);

  async function save() {
    if (!editing) return;
    try {
      const meta = { ...editing };
      delete meta.detected; // server keeps what it detected
      await api(`/documents/${doc.id}`, { method: "PATCH", body: { meta } });
      toast.success("Đã cập nhật thông tin đề và các câu của đề");
      setEditing(null);
      onSaved();
    } catch (e) {
      setErrors(e instanceof ApiError && e.fields ? e.fields : {});
      setError(e instanceof ApiError ? e.message : "Không lưu được");
    }
  }

  return (
    <div className="mb-4 flex flex-wrap items-center gap-2 rounded-lg border bg-muted/30 px-3 py-2 text-sm" data-testid="document-info">
      <ScanText className="size-4 text-muted-foreground" />
      <span className="text-muted-foreground">{detected ? "Nhận từ tiêu đề đề thi:" : "Không đọc được tiêu đề đề thi."}</span>
      {detected && <span className="font-medium">{detected}</span>}
      <Button variant="outline" size="xs" className="ml-auto" onClick={() => (setErrors({}), setError(null), setEditing(doc.meta))}>
        <Pencil /> Sửa thông tin
      </Button>
      <FormDialog open={!!editing} title="Thông tin đề" description="Áp dụng cho mọi câu của đề này" wide onOpenChange={(o) => !o && setEditing(null)}>
        {editing && (
          <div className="space-y-4">
            <DocumentMetaFields value={editing} onChange={setEditing} taxonomy={taxonomy} years={years} errors={errors} />
            {error && !Object.keys(errors).length && <FormAlert>{error}</FormAlert>}
            <div className="flex justify-end">
              <Button onClick={() => void save()}>Lưu</Button>
            </div>
          </div>
        )}
      </FormDialog>
    </div>
  );
}
