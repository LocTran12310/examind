"use client";

import { useState } from "react";
import { QuestionView } from "@/components/question/QuestionView";
import { draftOf, QuestionFields, type Draft } from "@/components/review/QuestionEditor";
import { FormAlert } from "@/components/app/FormAlert";
import { Button } from "@/components/ui/button";
import { FormField } from "@/components/app/FormField";
import { FormDialog } from "@/components/app/FormDialog";
import { NativeSelect, NativeSelectOption } from "@/components/ui/native-select";
import { ApiError } from "@/lib/api";
import { DIFFICULTY_LABEL, TAG_GROUP_LABEL, type ParsedQuestion, type Question, type Tag, type Taxonomy, type Topic } from "@/lib/types";
import { TopicPicker, topicLabel } from "./TopicPicker";

export interface QuestionFormValue extends Draft {
  difficulty: string | null;
  grade: number | null;
  subject_id: string | null;
  primary_topic_id: string | null;
  tag_ids: string[];
}

export function formValueOf(q?: ParsedQuestion): QuestionFormValue {
  const base = q ? draftOf(q) : { type: "mcq" as const, stem: "", options: "ABCD".split("").map((label) => ({ label, content: "" })), answer: null, solution: "" };
  return {
    ...base,
    difficulty: q?.difficulty ?? null,
    grade: q?.grade ?? null,
    subject_id: q?.subject_id ?? null,
    primary_topic_id: q?.topics.find((t) => t.is_primary)?.id ?? null,
    tag_ids: q?.tags.map((t) => t.id) ?? [],
  };
}

export function QuestionForm({
  initial,
  taxonomy,
  topics,
  tags,
  submitLabel,
  onSubmit,
  onCancel,
}: {
  initial: QuestionFormValue;
  taxonomy: Taxonomy;
  topics: Topic[];
  tags: Tag[];
  submitLabel: string;
  onSubmit: (v: QuestionFormValue) => Promise<void>;
  onCancel?: () => void;
}) {
  const [v, setV] = useState(initial);
  const [picking, setPicking] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const byId = new Map(topics.map((t) => [t.id, t]));
  const topic = v.primary_topic_id ? byId.get(v.primary_topic_id) : undefined;

  async function submit() {
    setBusy(true);
    setError(null);
    try {
      await onSubmit(v);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Không lưu được");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div
      className="grid gap-6 lg:grid-cols-2"
      onKeyDown={(e) => {
        if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
          e.preventDefault();
          void submit();
        }
      }}
    >
      <div className="space-y-4">
        <QuestionFields draft={v} setDraft={(d) => setV({ ...v, ...d })} />
        <div className="grid gap-3 sm:grid-cols-3">
          <FormField label="Môn">
            <NativeSelect className="w-full" value={v.subject_id ?? ""} onChange={(e) => setV({ ...v, subject_id: e.target.value || null })}>
              <NativeSelectOption value="">—</NativeSelectOption>
              {taxonomy.subjects.map((s) => (
                <NativeSelectOption key={s.id} value={s.id}>
                  {s.name}
                </NativeSelectOption>
              ))}
            </NativeSelect>
          </FormField>
          <FormField label="Lớp">
            <NativeSelect className="w-full" value={v.grade ?? ""} onChange={(e) => setV({ ...v, grade: e.target.value ? Number(e.target.value) : null })}>
              <NativeSelectOption value="">—</NativeSelectOption>
              {taxonomy.grades.map((g) => (
                <NativeSelectOption key={g.id} value={g.level}>
                  {g.name}
                </NativeSelectOption>
              ))}
            </NativeSelect>
          </FormField>
          <FormField label="Mức độ">
            <NativeSelect className="w-full" value={v.difficulty ?? ""} onChange={(e) => setV({ ...v, difficulty: e.target.value || null })}>
              <NativeSelectOption value="">—</NativeSelectOption>
              {Object.entries(DIFFICULTY_LABEL).map(([k, l]) => (
                <NativeSelectOption key={k} value={k}>
                  {l}
                </NativeSelectOption>
              ))}
            </NativeSelect>
          </FormField>
        </div>
        <FormField label="Chuyên đề chính">
          <div className="flex items-center gap-2">
            <Button variant="outline" onClick={() => setPicking(true)} data-testid="pick-topic">
              {topic ? topicLabel(topic, byId) : "Chọn chuyên đề"}
            </Button>
          </div>
        </FormField>
        <FormField label="Tags">
          <div className="flex flex-wrap gap-2 text-sm" data-testid="tag-options">
            {tags.map((t) => (
              <label key={t.id} className="flex items-center gap-1 rounded border border-border px-2 py-0.5">
                <input
                  type="checkbox"
                  checked={v.tag_ids.includes(t.id)}
                  onChange={(e) => setV({ ...v, tag_ids: e.target.checked ? [...v.tag_ids, t.id] : v.tag_ids.filter((x) => x !== t.id) })}
                />
                {t.name} <span className="text-xs text-muted-foreground/70">{TAG_GROUP_LABEL[t.group]}</span>
              </label>
            ))}
          </div>
        </FormField>
        {error && <FormAlert>{error}</FormAlert>}
        <div className="flex justify-end gap-2">
          {onCancel && <Button variant="outline" onClick={onCancel}>Hủy</Button>}
          <Button onClick={() => void submit()} disabled={busy}>
            {submitLabel} (Ctrl+Enter)
          </Button>
        </div>
      </div>
      <div className="rounded-xl border border-dashed border-input bg-card p-4" data-testid="preview">
        <QuestionView question={{ ...v, id: "preview", status: "approved" } as Question} mode="review" solutionOpen />
      </div>
      <FormDialog open={picking} title="Chọn chuyên đề" onOpenChange={(o) => !o && setPicking(false)}>
        <TopicPicker
          topics={topics}
          onPick={(t) => {
            setPicking(false);
            setV({ ...v, primary_topic_id: t.id });
          }}
          onClose={() => setPicking(false)}
        />
      </FormDialog>
    </div>
  );
}

export function payloadOf(v: QuestionFormValue) {
  return {
    type: v.type, stem: v.stem, options: v.options, answer: v.answer ?? {}, solution: v.solution, difficulty: v.difficulty ?? "",
    grade: v.grade ?? 0, subject_id: v.subject_id, primary_topic_id: v.primary_topic_id, tag_ids: v.tag_ids,
    topic_ids: v.primary_topic_id ? [v.primary_topic_id] : [],
  };
}
