"use client";

import { Pencil, ScanText } from "lucide-react";
import { FormAlert } from "@/components/common/FormAlert/FormAlert";
import { FormDialog } from "@/components/common/FormDialog/FormDialog";
import { DocumentMetaFields } from "@/components/common/DocumentMetaFields/DocumentMetaFields";
import { Button } from "@/components/ui/button";
import { useDocumentInfo } from "@/hooks/page-hooks/document-detail/use-document-info";
import type { SourceDocument } from "@/interfaces/document.interface";
import type { Taxonomy } from "@/interfaces/taxonomy.interface";

/** "Nhận từ tiêu đề đề thi: …" + edit the document's subject / grade / đợt / năm học / nguồn. */
export function DocumentInfo({ doc, taxonomy, onSaved = () => {} }: { doc: SourceDocument; taxonomy: Taxonomy; onSaved?: () => void }) {
  const p = useDocumentInfo(doc, onSaved);
  return (
    <div className="mb-4 flex flex-wrap items-center gap-2 rounded-lg border bg-muted/30 px-3 py-2 text-sm" data-testid="document-info">
      <ScanText className="size-4 text-muted-foreground" />
      <span className="text-muted-foreground">{p.detected ? "Nhận từ tiêu đề đề thi:" : "Không đọc được tiêu đề đề thi."}</span>
      {p.detected && <span className="font-medium">{p.detected}</span>}
      <Button variant="outline" size="xs" className="ml-auto" onClick={p.start}>
        <Pencil /> Sửa thông tin
      </Button>
      <FormDialog open={!!p.editing} title="Thông tin đề" description="Áp dụng cho mọi câu của đề này" wide onOpenChange={(o) => !o && p.setEditing(null)}>
        {p.editing && (
          <div className="space-y-4">
            <DocumentMetaFields value={p.editing} onChange={p.setEditing} taxonomy={taxonomy} years={p.years} errors={p.fields} />
            {p.message && !Object.keys(p.fields).length && <FormAlert>{p.message}</FormAlert>}
            <div className="flex justify-end">
              <Button onClick={p.save}>Lưu</Button>
            </div>
          </div>
        )}
      </FormDialog>
    </div>
  );
}
