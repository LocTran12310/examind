"use client";

import { useState } from "react";
import { FormField } from "@/components/common/FormField/FormField";
import { OptionSelect } from "@/components/common/OptionSelect/OptionSelect";
import { MarkdownEditor } from "@/components/common/MarkdownEditor/MarkdownEditor";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { useUploadAssetMutation } from "@/hooks/react-query/use-query-asset";
import type { Question, QuestionOption, QuestionType } from "@/interfaces/question.interface";

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

function MdArea({ label, value, onChange, rows = 3, testId }: { label: string; value: string; onChange: (v: string) => void; rows?: number; testId?: string }) {
  const [uploading, setUploading] = useState(false);
  const upload = useUploadAssetMutation();
  async function insertFiles(files: File[], at: number) {
    const images = files.filter((f) => f.type.startsWith("image/"));
    if (!images.length) return;
    setUploading(true);
    try {
      // each image becomes a markdown link to the uploaded asset
      const refs = await Promise.all(images.map(async (f) => `![](${(await upload.mutateAsync(f)).ref})`));
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
        {(f) => (
          <OptionSelect
            {...f}
            value={draft.type}
            onValueChange={(v) => {
              const type = v as QuestionType;
              setDraft({ ...draft, type, options: draft.options.length && (type === "mcq" || type === "true_false") ? draft.options : defaultOptions(type), answer: null });
            }}
            options={TYPES.map(([k, v]) => ({ value: k, label: v }))}
          />
        )}
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
              <OptionSelect
                aria-label={`Đúng/sai ${o.label}`}
                className="w-20"
                value={o.is_true === true ? "d" : o.is_true === false ? "s" : ""}
                onValueChange={(s) => {
                  const v = s === "d" ? true : s === "s" ? false : null;
                  const options = draft.options.map((x, j) => (j === i ? { ...x, is_true: v } : x));
                  setDraft({ ...draft, options, answer: Object.fromEntries(options.map((x) => [x.label, x.is_true ?? null])) as Question["answer"] });
                }}
                emptyLabel="?"
                options={[
                  { value: "d", label: "Đ" },
                  { value: "s", label: "S" },
                ]}
              />
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
