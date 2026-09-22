import { useState } from "react";
import { toast } from "sonner";
import { useYear } from "@/hooks/common/use-year";
import { useUpdateDocumentMutation } from "@/hooks/react-query/use-query-document";
import type { DocumentMeta, SourceDocument } from "@/interfaces/document.interface";
import { detectedLabel } from "@/lib/common/document-label";
import { formErrors } from "@/lib/common/form-errors";
import { ApiError } from "@/lib/common/http";

/** What the exam header said, and the dialog editing the document's metadata (applied to its questions). */
export function useDocumentInfo(doc: SourceDocument, onSaved: () => void) {
  const [editing, setEditing] = useState<DocumentMeta | null>(null);
  const { years } = useYear();
  const update = useUpdateDocumentMutation();
  const { fields } = formErrors(update.error);
  const message = update.error ? (update.error instanceof ApiError ? update.error.message : "Không lưu được") : null;
  return {
    detected: detectedLabel(doc.meta.detected),
    years,
    editing,
    setEditing,
    fields,
    message,
    start: () => {
      update.reset();
      setEditing(doc.meta);
    },
    save: () => {
      if (!editing) return;
      const meta = { ...editing };
      delete meta.detected; // server keeps what it detected
      update.mutate(
        { id: doc.id, body: { meta } },
        {
          onSuccess: () => {
            toast.success("Đã cập nhật thông tin đề và các câu của đề");
            setEditing(null);
            onSaved();
          },
        },
      );
    },
  };
}
