"use client";

import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { useState } from "react";
import { MarkdownEditor } from "@/components/question/MarkdownEditor";
import { useSaveHint, useSaveShortcut } from "@/lib/shortcuts";
import { QuestionView } from "@/components/question/QuestionView";
import { FormAlert } from "@/components/app/FormAlert";
import { Button } from "@/components/ui/button";
import { FormField } from "@/components/app/FormField";
import { Input } from "@/components/ui/input";
import { Kbd } from "@/components/ui/kbd";
import { Label } from "@/components/ui/label";
import { NativeSelect, NativeSelectOption } from "@/components/ui/native-select";
import { api, ApiError } from "@/lib/api";
import type { ParsedQuestion, Question, QuestionOption, QuestionType } from "@/lib/types";

const TYPES: [QuestionType, string][] = [
  ["mcq", "Trắc nghiệm 4 phương án"],
  ["true_false", "Đúng / Sai (4 mệnh đề)"],
  ["short_answer", "Trả lời ngắn"],
  ["essay", "Tự luận"],
];

export interface Draft {
  type: QuestionType;
  stem: string;
  options: QuestionOption[];
  answer: Question["answer"];
  solution: string;
}

export function draftOf(q: Pick<Question, "type" | "stem" | "options" | "answer" | "solution">): Draft {
  return { type: q.type, stem: q.stem, options: q.options.map((o) => ({ ...o })), answer: q.answer ? { ...q.answer } : null, solution: q.solution };
}

function defaultOptions(type: QuestionType): QuestionOption[] {
  if (type === "mcq") return "ABCD".split("").map((label) => ({ label, content: "" }));
  if (type === "true_false") return "abcd".split("").map((label) => ({ label, content: "", is_true: null }));
  return [];
}

/** Uploads a pasted/dropped image and returns the markdown to insert. */
export async function uploadImage(file: File): Promise<string> {
  const form = new FormData();
  form.append("file", file);
  const r = await api<{ ref: string }>("/assets", { form });
  return `![](${r.ref})`;
}

function MdArea({ label, value, onChange, rows = 3, testId }: { label: string; value: string; onChange: (v: string) => void; rows?: number; testId?: string }) {
  const [uploading, setUploading] = useState(false);
  async function insertFiles(files: File[], at: number) {
    const images = files.filter((f) => f.type.startsWith("image/"));
    if (!images.length) return;
    setUploading(true);
    try {
      const refs = await Promise.all(images.map(uploadImage));
      onChange(value.slice(0, at) + "\n" + refs.join("\n") + "\n" + value.slice(at));
    } finally {
      setUploading(false);
    }
  }
  return (
    <FormField label={label} hint="Markdown, công thức $…$ — xem trước ngay bên dưới; dán hoặc kéo thả ảnh">
      {(f) => <MarkdownEditor {...f} value={value} onChange={onChange} rows={rows} data-testid={testId} aria-label={label} onFiles={insertFiles} uploading={uploading} />}
    </FormField>
  );
}

export function QuestionFields({ draft, setDraft }: { draft: Draft; setDraft: (d: Draft) => void }) {
  const set = <K extends keyof Draft>(k: K, v: Draft[K]) => setDraft({ ...draft, [k]: v });
  const setOption = (i: number, patch: Partial<QuestionOption>) => set("options", draft.options.map((o, j) => (j === i ? { ...o, ...patch } : o)));
  return (
    <div className="space-y-3">
      <FormField label="Loại câu">
        <NativeSelect
          className="w-full"
          value={draft.type}
          onChange={(e) => {
            const type = e.target.value as QuestionType;
            setDraft({ ...draft, type, options: draft.options.length && (type === "mcq" || type === "true_false") ? draft.options : defaultOptions(type), answer: null });
          }}
        >
          {TYPES.map(([k, v]) => (
            <NativeSelectOption key={k} value={k}>
              {v}
            </NativeSelectOption>
          ))}
        </NativeSelect>
      </FormField>
      <MdArea label="Đề bài" value={draft.stem} onChange={(v) => set("stem", v)} rows={4} testId="stem" />
      {(draft.type === "mcq" || draft.type === "true_false") && (
        <RadioGroup className="grid gap-2" value={draft.type === "mcq" ? (draft.answer?.key ?? "") : ""} onValueChange={(k) => set("answer", { key: k })}>
        {draft.options.map((o, i) => (
          <div key={i} className="flex items-start gap-2">
            <Input aria-label={`Nhãn ${i + 1}`} className="w-12" value={o.label} onChange={(e) => setOption(i, { label: e.target.value })} />
            <div className="flex-1">
              <MarkdownEditor compact aria-label={`Phương án ${o.label}`} rows={1} value={o.content} onChange={(v) => setOption(i, { content: v })} />
            </div>
            {draft.type === "mcq" ? (
              <Label className="mt-2 gap-1 font-normal">
                <RadioGroupItem value={o.label} aria-label={`${o.label} đúng`} /> đúng
              </Label>
            ) : (
              <NativeSelect
                aria-label={`Đúng/sai ${o.label}`}
                value={o.is_true === true ? "d" : o.is_true === false ? "s" : ""}
                onChange={(e) => {
                  const v = e.target.value === "d" ? true : e.target.value === "s" ? false : null;
                  const options = draft.options.map((x, j) => (j === i ? { ...x, is_true: v } : x));
                  setDraft({ ...draft, options, answer: Object.fromEntries(options.map((x) => [x.label, x.is_true ?? null])) as Question["answer"] });
                }}
              >
                <NativeSelectOption value="">?</NativeSelectOption>
                <NativeSelectOption value="d">Đ</NativeSelectOption>
                <NativeSelectOption value="s">S</NativeSelectOption>
              </NativeSelect>
            )}
          </div>
        ))}
        </RadioGroup>
      )}
      {draft.type === "short_answer" && (
        <FormField label="Đáp án">
          <Input value={(draft.answer?.value as string) ?? ""} onChange={(e) => set("answer", e.target.value ? { value: e.target.value } : null)} />
        </FormField>
      )}
      {draft.type === "essay" && (
        <MdArea label="Đáp án mẫu" value={(draft.answer?.text as string) ?? ""} onChange={(v) => set("answer", v ? { text: v } : null)} />
      )}
      <MdArea label="Lời giải" value={draft.solution} onChange={(v) => set("solution", v)} rows={4} testId="solution" />
    </div>
  );
}

export function QuestionEditor({ question, onSaved, onCancel }: { question: ParsedQuestion; onSaved: (q: ParsedQuestion) => void; onCancel: () => void }) {
  const [draft, setDraft] = useState<Draft>(draftOf(question));
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  useSaveShortcut(() => {
    if (!busy) void save();
  });
  const hint = useSaveHint();

  async function save() {
    setBusy(true);
    setError(null);
    try {
      const body = { type: draft.type, stem: draft.stem, options: draft.options, answer: draft.answer ?? {}, solution: draft.solution };
      onSaved(await api<ParsedQuestion>(`/questions/${question.id}`, { method: "PATCH", body }));
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Không lưu được");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div
      className="grid gap-4 lg:grid-cols-2"
      data-testid="editor"
      onKeyDown={(e) => {
        if (e.key === "Escape") onCancel();
      }}
    >
      <div>
        <QuestionFields draft={draft} setDraft={setDraft} />
        {error && <div className="mt-2"><FormAlert>{error}</FormAlert></div>}
        <div className="mt-3 flex justify-end gap-2">
          <Button variant="outline" onClick={onCancel}>Hủy (Esc)</Button>
          <Button onClick={() => void save()} disabled={busy}>
            Lưu <Kbd className="ml-1 h-4 bg-primary-foreground/20 text-[10px] text-current">{hint}</Kbd>
          </Button>
        </div>
      </div>
      <div className="rounded-lg border border-dashed border-input p-3" data-testid="preview">
        <QuestionView question={{ ...question, ...draft } as Question} mode="review" solutionOpen />
      </div>
    </div>
  );
}
