import { useRef, useState } from "react";
import { UPLOAD_ACCEPTED } from "@/constants/document.constant";
import { useYear } from "@/hooks/common/use-year";
import { useCheckDocumentsMutation, useUploadDocumentMutation } from "@/hooks/react-query/use-query-document";
import type { DocumentMeta, DuplicateCheck, DuplicateChoice, ProcessingConfig, SourceDocument } from "@/interfaces/document.interface";
import { ApiError } from "@/lib/common/http";
import { defaultChoice, sha256, skipped, type UploadRow } from "@/lib/page-libs/documents/upload-rows";

export interface UploadFormOptions {
  onUploaded?: (doc: SourceDocument, duplicate: boolean) => void;
  /** After the whole batch: every file that reached the server. */
  onFinished?: (done: { doc: SourceDocument; duplicate: boolean }[]) => void;
  config?: Partial<ProcessingConfig>;
}

/** Upload one or many exam files with the same settings (official-exam-ingestion AC-10): each file is
 *  hashed in the browser and checked for duplicates first; conflicting files get a choice. */
export function useUploadForm({ onUploaded, onFinished, config }: UploadFormOptions) {
  const [rows, setRows] = useState<UploadRow[]>([]);
  const [drag, setDrag] = useState(false);
  const { years } = useYear();
  const [meta, setMeta] = useState<DocumentMeta>({});
  const [fields, setFields] = useState<Record<string, string>>({});
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const input = useRef<HTMLInputElement>(null);
  const check = useCheckDocumentsMutation();
  const upload = useUploadDocumentMutation();

  const patch = (i: number, p: Partial<UploadRow>) => setRows((r) => r.map((x, j) => (j === i ? { ...x, ...p } : x)));

  /** Ask the server which files are already here (same content) or share a name (critical: no silent duplicates). */
  async function probe(files: File[]) {
    let found: DuplicateCheck[] = [];
    try {
      const probes = await Promise.all(files.map(async (f) => ({ name: f.name, size: f.size, sha256: await sha256(f) })));
      found = await check.mutateAsync({ files: probes });
    } catch {
      found = [];
    }
    setRows((rs) =>
      rs.map((r) => {
        const i = files.indexOf(r.file);
        if (i < 0) return r;
        const c = found[i];
        return c && (c.same_file || c.same_name.length) ? { ...r, state: "waiting", conflict: c, choice: defaultChoice(c) } : { ...r, state: "waiting" };
      }),
    );
  }

  function add(list: FileList | File[] | null | undefined) {
    const files = [...(list ?? [])];
    const ignored = files.filter((f) => !UPLOAD_ACCEPTED.test(f.name) && files.length > 1).length;
    const keep = files.length > 1 ? files.filter((f) => UPLOAD_ACCEPTED.test(f.name)) : files;
    const fresh: UploadRow[] = keep.map((file) => ({ file, state: "checking" }));
    setRows((r) => [...r.filter((x) => x.state === "waiting" || x.state === "error" || x.state === "checking"), ...fresh]);
    setFields({});
    setError(ignored ? `Bỏ qua ${ignored} file không phải .docx, .pdf hoặc ảnh` : null);
    void probe(keep);
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (rows.some((r) => r.state === "checking")) return;
    const pending = rows.map((r, i) => [r, i] as const).filter(([r]) => r.state === "waiting" || r.state === "error");
    if (!pending.length) return setFields({ file: "Chọn file đề" });
    // "Bỏ qua" rows are settled without a request
    for (const [r, i] of pending) if (skipped(r)) patch(i, { state: "skipped", doc: undefined });
    const todo = pending.filter(([r]) => !skipped(r));
    setBusy(true);
    setError(null);
    setFields({});
    const done: { doc: SourceDocument; duplicate: boolean }[] = [];
    for (const [row, i] of todo) {
      patch(i, { state: "sending", message: undefined });
      const choice = row.conflict ? row.choice : undefined;
      const replaceId = choice === "replace" && row.conflict && !row.conflict.same_file ? row.conflict.same_name[0]?.id : undefined;
      try {
        const r = await upload.mutateAsync({ file: row.file, meta, config: config ?? {}, on_duplicate: choice, replace_id: replaceId });
        patch(i, { state: r.action === "replaced" || r.action === "reparsed" ? "replaced" : r.duplicate ? "duplicate" : "queued", doc: r.document });
        done.push({ doc: r.document, duplicate: r.duplicate });
        onUploaded?.(r.document, r.duplicate);
      } catch (err) {
        const message = err instanceof ApiError ? (err.fields?.file ?? err.message) : "Tải lên thất bại";
        patch(i, { state: "error", message });
        if (todo.length === 1 && err instanceof ApiError && err.fields) setFields(err.fields);
      }
    }
    if (input.current) input.current.value = "";
    setBusy(false);
    if (done.length) onFinished?.(done);
  }

  return {
    rows,
    input,
    drag,
    setDrag,
    years,
    meta,
    setMeta,
    fields,
    error,
    busy,
    waiting: rows.filter((r) => (r.state === "waiting" || r.state === "error") && !skipped(r)).length,
    conflicts: rows.filter((r) => r.conflict && r.state === "waiting").length,
    checking: rows.some((r) => r.state === "checking"),
    add,
    submit,
    remove: (i: number) => setRows((x) => x.filter((_, j) => j !== i)),
    setChoice: (i: number, choice: DuplicateChoice) => patch(i, { choice }),
    setAll: (choice: DuplicateChoice) =>
      setRows((rs) => rs.map((r) => (r.conflict && r.state === "waiting" && (choice !== "keep_both" || !r.conflict.same_file) ? { ...r, choice } : r))),
  };
}
