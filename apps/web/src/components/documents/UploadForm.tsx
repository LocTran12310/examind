"use client";

import { cn } from "@/lib/utils";
import { useRef, useState } from "react";
import { currentSchoolYear } from "@/components/org/ClassForms";
import { FormAlert } from "@/components/app/FormAlert";
import { Button } from "@/components/ui/button";
import { FormField } from "@/components/app/FormField";
import { Input } from "@/components/ui/input";
import { NativeSelect, NativeSelectOption } from "@/components/ui/native-select";
import { api, ApiError } from "@/lib/api";
import { EXAM_KINDS, type DocumentMeta, type ProcessingConfig, type SourceDocument, type Taxonomy } from "@/lib/types";

const ACCEPT = ".docx,.pdf,.png,.jpg,.jpeg";

export function UploadForm({
  taxonomy,
  onUploaded,
  config,
  configSlot,
}: {
  taxonomy: Taxonomy;
  onUploaded: (doc: SourceDocument, duplicate: boolean) => void;
  config?: Partial<ProcessingConfig>;
  configSlot?: React.ReactNode;
}) {
  const math = taxonomy.subjects.find((s) => s.code === "toan") ?? taxonomy.subjects[0];
  const [file, setFile] = useState<File | null>(null);
  const [drag, setDrag] = useState(false);
  const [meta, setMeta] = useState<DocumentMeta>({ subject_id: math?.id, semester_code: "hk1", exam_kind: "Giữa kỳ", school_year: currentSchoolYear() });
  const [fields, setFields] = useState<Record<string, string>>({});
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const input = useRef<HTMLInputElement>(null);
  const set = (k: keyof DocumentMeta, v: string | number | undefined) => setMeta((m) => ({ ...m, [k]: v === "" ? undefined : v }));

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!file) return setFields({ file: "Chọn file đề" });
    setBusy(true);
    setError(null);
    setFields({});
    const form = new FormData();
    form.append("file", file);
    form.append("meta", JSON.stringify(meta));
    form.append("config", JSON.stringify(config ?? {}));
    try {
      const r = await api<{ document: SourceDocument; duplicate: boolean }>("/documents", { form });
      setFile(null);
      if (input.current) input.current.value = "";
      onUploaded(r.document, r.duplicate);
    } catch (err) {
      if (err instanceof ApiError && err.fields) setFields(err.fields);
      setError(err instanceof ApiError ? err.message : "Tải lên thất bại");
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={submit} className="space-y-4">
      <div
        onDragOver={(e) => (e.preventDefault(), setDrag(true))}
        onDragLeave={() => setDrag(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDrag(false);
          setFile(e.dataTransfer.files?.[0] ?? null);
        }}
        className={cn("rounded-xl border-2 border-dashed p-6 text-center text-sm", drag ? "border-primary bg-primary/10" : "border-input")}
      >
        <p className="mb-2 text-muted-foreground">{file ? <b>{file.name}</b> : "Kéo thả file đề vào đây (.docx, .pdf, ảnh chụp)"}</p>
        <input ref={input} data-testid="file" type="file" accept={ACCEPT} className="mx-auto block text-sm" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
        {fields.file && <p className="mt-2 text-xs text-destructive">{fields.file}</p>}
      </div>
      <div className="grid gap-3 sm:grid-cols-3">
        <FormField label="Môn" error={fields.subject_id}>
          <NativeSelect className="w-full" value={meta.subject_id ?? ""} onChange={(e) => set("subject_id", e.target.value)}>
            {taxonomy.subjects.map((s) => (
              <NativeSelectOption key={s.id} value={s.id}>
                {s.name}
              </NativeSelectOption>
            ))}
          </NativeSelect>
        </FormField>
        <FormField label="Lớp" error={fields.grade}>
          <NativeSelect className="w-full" value={meta.grade ?? ""} onChange={(e) => set("grade", e.target.value ? Number(e.target.value) : undefined)}>
            <NativeSelectOption value="">—</NativeSelectOption>
            {taxonomy.grades.map((g) => (
              <NativeSelectOption key={g.id} value={g.level}>
                {g.name}
              </NativeSelectOption>
            ))}
          </NativeSelect>
        </FormField>
        <FormField label="Học kỳ" error={fields.semester_code}>
          <NativeSelect className="w-full" value={meta.semester_code ?? ""} onChange={(e) => set("semester_code", e.target.value)}>
            <NativeSelectOption value="">—</NativeSelectOption>
            {taxonomy.semesters.map((s) => (
              <NativeSelectOption key={s.id} value={s.code}>
                {s.name}
              </NativeSelectOption>
            ))}
          </NativeSelect>
        </FormField>
        <FormField label="Loại đề" error={fields.exam_kind}>
          <NativeSelect className="w-full" value={meta.exam_kind ?? ""} onChange={(e) => set("exam_kind", e.target.value)}>
            <NativeSelectOption value="">—</NativeSelectOption>
            {EXAM_KINDS.map((k) => (
              <NativeSelectOption key={k}>{k}</NativeSelectOption>
            ))}
          </NativeSelect>
        </FormField>
        <FormField label="Năm học" error={fields.school_year}>
          <Input value={meta.school_year ?? ""} onChange={(e) => set("school_year", e.target.value)} />
        </FormField>
        <FormField label="Nguồn đề" error={fields.source_name} hint="Ví dụ: THPT Chu Văn An">
          <Input value={meta.source_name ?? ""} onChange={(e) => set("source_name", e.target.value)} />
        </FormField>
      </div>
      {configSlot}
      {error && !Object.keys(fields).length && <FormAlert>{error}</FormAlert>}
      <div className="flex justify-end">
        <Button type="submit" disabled={busy}>
          {busy ? "Đang tải lên…" : "Tải lên và tách câu"}
        </Button>
      </div>
    </form>
  );
}
