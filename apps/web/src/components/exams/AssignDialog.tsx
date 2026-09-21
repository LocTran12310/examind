"use client";

import { useState } from "react";
import { Alert, Button, Field, Input, Select } from "@/components/ui";
import { api } from "@/lib/api";
import { fromLocalInput, toLocalInput } from "@/lib/dates";
import { useMutation } from "@/lib/hooks";
import type { Assignment, ResultsPolicy, SchoolClass } from "@/lib/types";

export function AssignDialog({ examId, title, classes, onDone }: { examId: string; title: string; classes: SchoolClass[]; onDone: (a: Assignment) => void }) {
  const [v, setV] = useState({
    title,
    open_at: toLocalInput(new Date()),
    close_at: toLocalInput(new Date(Date.now() + 7 * 86400_000)),
    duration_minutes: 45,
    max_attempts: 1,
    shuffle_questions: true,
    shuffle_options: true,
    results_policy: "after_submit" as ResultsPolicy,
    class_ids: [] as string[],
  });
  const m = useMutation();
  const set = <K extends keyof typeof v>(k: K, val: (typeof v)[K]) => setV((x) => ({ ...x, [k]: val }));
  return (
    <form
      className="space-y-4"
      onSubmit={async (e) => {
        e.preventDefault();
        const r = await m.run(() =>
          api<Assignment>("/assignments", { body: { ...v, exam_id: examId, open_at: fromLocalInput(v.open_at), close_at: fromLocalInput(v.close_at) } }),
        );
        if (r) onDone(r);
      }}
    >
      {m.message && <Alert>{m.message}</Alert>}
      <Field label="Tên bài" error={m.fields.title}>
        <Input value={v.title} onChange={(e) => set("title", e.target.value)} />
      </Field>
      <Field label="Lớp" error={m.fields.class_ids}>
        <div className="flex flex-wrap gap-2 text-sm" data-testid="class-options">
          {classes.map((c) => (
            <label key={c.id} className="flex items-center gap-1 rounded border border-gray-200 px-2 py-1">
              <input
                type="checkbox"
                checked={v.class_ids.includes(c.id)}
                onChange={(e) => set("class_ids", e.target.checked ? [...v.class_ids, c.id] : v.class_ids.filter((x) => x !== c.id))}
              />
              {c.name} <span className="text-xs text-gray-400">({c.member_count})</span>
            </label>
          ))}
        </div>
      </Field>
      <div className="grid gap-3 sm:grid-cols-2">
        <Field label="Mở lúc" error={m.fields.open_at}>
          <Input type="datetime-local" value={v.open_at} onChange={(e) => set("open_at", e.target.value)} />
        </Field>
        <Field label="Đóng lúc" error={m.fields.close_at}>
          <Input type="datetime-local" value={v.close_at} onChange={(e) => set("close_at", e.target.value)} />
        </Field>
        <Field label="Thời gian làm (phút)" error={m.fields.duration_minutes}>
          <Input type="number" min={1} max={600} value={v.duration_minutes} onChange={(e) => set("duration_minutes", Number(e.target.value))} />
        </Field>
        <Field label="Số lượt làm" error={m.fields.max_attempts}>
          <Input type="number" min={1} max={20} value={v.max_attempts} onChange={(e) => set("max_attempts", Number(e.target.value))} />
        </Field>
        <Field label="Xem kết quả">
          <Select className="w-full" value={v.results_policy} onChange={(e) => set("results_policy", e.target.value as ResultsPolicy)}>
            <option value="after_submit">Ngay sau khi nộp</option>
            <option value="after_close">Sau khi đóng bài</option>
            <option value="never">Chỉ xem điểm</option>
          </Select>
        </Field>
        <div className="space-y-1 pt-6 text-sm">
          <label className="flex items-center gap-2">
            <input type="checkbox" checked={v.shuffle_questions} onChange={(e) => set("shuffle_questions", e.target.checked)} /> Đảo thứ tự câu
          </label>
          <label className="flex items-center gap-2">
            <input type="checkbox" checked={v.shuffle_options} onChange={(e) => set("shuffle_options", e.target.checked)} /> Đảo phương án
          </label>
        </div>
      </div>
      <div className="flex justify-end">
        <Button variant="primary" type="submit" disabled={m.busy || !v.class_ids.length}>
          Giao bài
        </Button>
      </div>
    </form>
  );
}
