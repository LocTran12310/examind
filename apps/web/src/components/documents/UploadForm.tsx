"use client";

import { CheckCircle2, CircleAlert, Copy, Loader2, X } from "lucide-react";
import { useRef, useState } from "react";
import { FormAlert } from "@/components/app/FormAlert";
import { useYear } from "@/components/app/YearContext";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { api, ApiError } from "@/lib/api";
import { type DocumentMeta, type ProcessingConfig, type SourceDocument, type Taxonomy } from "@/lib/types";
import { cn } from "@/lib/utils";
import { DocumentMetaFields } from "./DocumentMetaFields";
import { OptionSelect } from "@/components/app/OptionSelect";
import { formatDateTime } from "@/lib/datetime";

const ACCEPT = ".docx,.pdf,.png,.jpg,.jpeg";
const ACCEPTED = /\.(docx|pdf|png|jpe?g)$/i;

type Choice = "skip" | "replace" | "keep_both";
type Brief = { id: string; filename: string; status: string; question_count: number; created_at: string };
type Conflict = { same_file: Brief | null; same_name: Brief[] };
type Row = {
  file: File;
  state: "checking" | "waiting" | "sending" | "queued" | "duplicate" | "replaced" | "skipped" | "error";
  message?: string;
  doc?: SourceDocument;
  conflict?: Conflict;
  choice?: Choice;
};

async function sha256(file: File): Promise<string> {
  const buf = await file.arrayBuffer();
  const hash = await crypto.subtle.digest("SHA-256", buf);
  return [...new Uint8Array(hash)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

/** Default: the same content is skipped; a new version of a same-name file replaces the newest one. */
const defaultChoice = (c: Conflict): Choice | undefined => (c.same_file ? "skip" : c.same_name.length ? "replace" : undefined);

/** Upload one or many exam files with the same settings (official-exam-ingestion AC-10).
 *  Fields left on "Tự nhận từ đề" are filled from each file's header. */
export function UploadForm({
  taxonomy,
  onUploaded,
  onFinished,
  config,
  configSlot,
}: {
  taxonomy: Taxonomy;
  onUploaded?: (doc: SourceDocument, duplicate: boolean) => void;
  /** After the whole batch: every file that reached the server. */
  onFinished?: (done: { doc: SourceDocument; duplicate: boolean }[]) => void;
  config?: Partial<ProcessingConfig>;
  configSlot?: React.ReactNode;
}) {
  const [rows, setRows] = useState<Row[]>([]);
  const [drag, setDrag] = useState(false);
  const { years } = useYear();
  const [meta, setMeta] = useState<DocumentMeta>({});
  const [fields, setFields] = useState<Record<string, string>>({});
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const input = useRef<HTMLInputElement>(null);

  function add(list: FileList | File[] | null | undefined) {
    const files = [...(list ?? [])];
    const skipped = files.filter((f) => !ACCEPTED.test(f.name) && files.length > 1).length;
    const keep = files.length > 1 ? files.filter((f) => ACCEPTED.test(f.name)) : files;
    const fresh: Row[] = keep.map((file) => ({ file, state: "checking" }));
    setRows((r) => [...r.filter((x) => x.state === "waiting" || x.state === "error" || x.state === "checking"), ...fresh]);
    setFields({});
    setError(skipped ? `Bỏ qua ${skipped} file không phải .docx, .pdf hoặc ảnh` : null);
    void check(keep);
  }

  /** Ask the server which files are already here (same content) or share a name (critical: no silent duplicates). */
  async function check(files: File[]) {
    let found: Conflict[] = [];
    try {
      const probes = await Promise.all(files.map(async (f) => ({ name: f.name, size: f.size, sha256: await sha256(f) })));
      found = await api<Conflict[]>("/documents/check", { body: { files: probes } });
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

  const setChoice = (i: number, choice: Choice) => patch(i, { choice });
  const setAll = (choice: Choice) =>
    setRows((rs) => rs.map((r) => (r.conflict && r.state === "waiting" && (choice !== "keep_both" || !r.conflict.same_file) ? { ...r, choice } : r)));

  const patch = (i: number, p: Partial<Row>) => setRows((r) => r.map((x, j) => (j === i ? { ...x, ...p } : x)));

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (rows.some((r) => r.state === "checking")) return;
    const pending = rows.map((r, i) => [r, i] as const).filter(([r]) => r.state === "waiting" || r.state === "error");
    if (!pending.length) return setFields({ file: "Chọn file đề" });
    // "Bỏ qua" rows are settled without a request
    for (const [r, i] of pending) if (r.conflict && r.choice === "skip") patch(i, { state: "skipped", doc: undefined });
    const todo = pending.filter(([r]) => !(r.conflict && r.choice === "skip"));
    setBusy(true);
    setError(null);
    setFields({});
    const done: { doc: SourceDocument; duplicate: boolean }[] = [];
    for (const [row, i] of todo) {
      patch(i, { state: "sending", message: undefined });
      const form = new FormData();
      form.append("file", row.file);
      form.append("meta", JSON.stringify(meta));
      form.append("config", JSON.stringify(config ?? {}));
      if (row.conflict && row.choice) {
        form.append("on_duplicate", row.choice);
        if (row.choice === "replace" && !row.conflict.same_file && row.conflict.same_name[0]) form.append("replace_id", row.conflict.same_name[0].id);
      }
      try {
        const r = await api<{ document: SourceDocument; duplicate: boolean; action: string }>("/documents", { form });
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

  const waiting = rows.filter((r) => (r.state === "waiting" || r.state === "error") && !(r.conflict && r.choice === "skip")).length;
  const conflicts = rows.filter((r) => r.conflict && r.state === "waiting").length;
  const checking = rows.some((r) => r.state === "checking");
  return (
    <form onSubmit={submit} className="space-y-4">
      <div
        onDragOver={(e) => (e.preventDefault(), setDrag(true))}
        onDragLeave={() => setDrag(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDrag(false);
          add(e.dataTransfer.files);
        }}
        className={cn("rounded-xl border-2 border-dashed p-6 text-center text-sm", drag ? "border-primary bg-primary/10" : "border-input")}
      >
        <p className="mb-2 text-muted-foreground">Kéo thả một hoặc nhiều file đề vào đây (.docx, .pdf, ảnh chụp)</p>
        <Input ref={input} data-testid="file" type="file" multiple accept={ACCEPT} aria-label="Chọn file đề" className="mx-auto max-w-sm" onChange={(e) => add(e.target.files)} />
        {fields.file && <p className="mt-2 text-xs text-destructive">{fields.file}</p>}
      </div>
      {rows.length > 0 && (
        <ul className="divide-y rounded-lg border text-sm" aria-label="File đã chọn">
          {rows.map((r, i) => (
            <li key={`${r.file.name}-${i}`} className="grid gap-1 px-3 py-1.5" data-testid={`upload-row-${i}`}>
              <div className="flex items-center gap-2">
                <FileState row={r} />
                <span className="min-w-0 flex-1 truncate" title={r.file.name}>
                  {r.file.name}
                </span>
                <span className={cn("shrink-0 text-xs", r.state === "error" ? "text-destructive" : "text-muted-foreground")}>{stateLabel(r)}</span>
                {(r.state === "waiting" || r.state === "error") && !busy && (
                  <Button type="button" variant="ghost" size="icon-xs" aria-label={`Bỏ ${r.file.name}`} onClick={() => setRows((x) => x.filter((_, j) => j !== i))}>
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
                    onValueChange={(v) => setChoice(i, v as Choice)}
                    options={
                      r.conflict.same_file
                        ? [
                            { value: "skip", label: "Bỏ qua (dùng bản đã có)" },
                            { value: "replace", label: "Tách lại bản đã có" },
                          ]
                        : [
                            { value: "replace", label: "Ghi đè bản cũ" },
                            { value: "keep_both", label: "Giữ cả hai" },
                            { value: "skip", label: "Bỏ qua file này" },
                          ]
                    }
                  />
                </div>
              )}
            </li>
          ))}
        </ul>
      )}
      {conflicts > 1 && (
        <div className="flex flex-wrap items-center gap-2 text-sm">
          <span className="text-muted-foreground">{conflicts} file trùng:</span>
          <Button type="button" size="xs" variant="outline" onClick={() => setAll("skip")}>
            Bỏ qua tất cả
          </Button>
          <Button type="button" size="xs" variant="outline" onClick={() => setAll("replace")}>
            Ghi đè / tách lại tất cả
          </Button>
        </div>
      )}
      <DocumentMetaFields value={meta} onChange={setMeta} taxonomy={taxonomy} years={years} errors={fields} emptyLabel="Tự nhận từ đề" />
      {configSlot}
      {error && !Object.keys(fields).length && <FormAlert kind="warning">{error}</FormAlert>}
      <div className="flex justify-end">
        <Button type="submit" disabled={busy || checking}>
          {checking ? "Đang kiểm tra file trùng…" : busy ? "Đang tải lên…" : waiting > 1 ? `Tải lên ${waiting} file và tách câu` : "Tải lên và tách câu"}
        </Button>
      </div>
    </form>
  );
}

function stateLabel(r: Row): string {
  switch (r.state) {
    case "checking":
      return "Đang kiểm tra…";
    case "waiting":
      return r.conflict && r.choice === "skip" ? "Sẽ bỏ qua" : "Chờ tải lên";
    case "replaced":
      return "Đã ghi đè — đang tách lại";
    case "skipped":
      return "Đã bỏ qua";
    case "sending":
      return "Đang tải…";
    case "queued":
      return "Đã đưa vào hàng đợi";
    case "duplicate":
      return "Đã có — dùng bản cũ";
    default:
      return r.message ?? "Lỗi";
  }
}

function FileState({ row }: { row: Row }) {
  const cls = "size-4 shrink-0";
  if (row.state === "sending" || row.state === "checking") return <Loader2 className={cn(cls, "animate-spin text-muted-foreground")} />;
  if (row.state === "queued" || row.state === "replaced") return <CheckCircle2 className={cn(cls, "text-emerald-600")} />;
  if (row.state === "duplicate" || row.state === "skipped") return <Copy className={cn(cls, "text-amber-600")} />;
  if (row.state === "error") return <CircleAlert className={cn(cls, "text-destructive")} />;
  return <span className={cn(cls, "rounded-full border")} />;
}
