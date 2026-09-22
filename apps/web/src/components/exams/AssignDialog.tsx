"use client";

import { Checkbox } from "@/components/ui/checkbox";
import { useState } from "react";
import { FormAlert } from "@/components/app/FormAlert";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { FormField } from "@/components/app/FormField";
import { Input } from "@/components/ui/input";
import { NativeSelect, NativeSelectOption } from "@/components/ui/native-select";
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
      {m.message && <FormAlert>{m.message}</FormAlert>}
      <FormField label="Tên bài" error={m.fields.title}>
        <Input value={v.title} onChange={(e) => set("title", e.target.value)} />
      </FormField>
      <FormField label="Lớp" error={m.fields.class_ids}>
        <div className="flex flex-wrap gap-2 text-sm" data-testid="class-options">
          {classes.map((c) => (
            <Label key={c.id} className="gap-1.5 rounded border border-border px-2 py-1 font-normal">
              <Checkbox
                checked={v.class_ids.includes(c.id)}
                onCheckedChange={(on) => set("class_ids", on === true ? [...v.class_ids, c.id] : v.class_ids.filter((x) => x !== c.id))}
              />
              {c.name} <span className="text-xs text-muted-foreground/70">({c.member_count})</span>
            </Label>
          ))}
        </div>
      </FormField>
      <div className="grid gap-3 sm:grid-cols-2">
        <FormField label="Mở lúc" error={m.fields.open_at}>
          <Input type="datetime-local" value={v.open_at} onChange={(e) => set("open_at", e.target.value)} />
        </FormField>
        <FormField label="Đóng lúc" error={m.fields.close_at}>
          <Input type="datetime-local" value={v.close_at} onChange={(e) => set("close_at", e.target.value)} />
        </FormField>
        <FormField label="Thời gian làm (phút)" error={m.fields.duration_minutes}>
          <Input type="number" min={1} max={600} value={v.duration_minutes} onChange={(e) => set("duration_minutes", Number(e.target.value))} />
        </FormField>
        <FormField label="Số lượt làm" error={m.fields.max_attempts}>
          <Input type="number" min={1} max={20} value={v.max_attempts} onChange={(e) => set("max_attempts", Number(e.target.value))} />
        </FormField>
        <FormField label="Xem kết quả">
          <NativeSelect className="w-full" value={v.results_policy} onChange={(e) => set("results_policy", e.target.value as ResultsPolicy)}>
            <NativeSelectOption value="after_submit">Ngay sau khi nộp</NativeSelectOption>
            <NativeSelectOption value="after_close">Sau khi đóng bài</NativeSelectOption>
            <NativeSelectOption value="never">Chỉ xem điểm</NativeSelectOption>
          </NativeSelect>
        </FormField>
        <div className="space-y-1 pt-6 text-sm">
          <Label className="font-normal">
            <Checkbox checked={v.shuffle_questions} onCheckedChange={(v) => set("shuffle_questions", v === true)} /> Đảo thứ tự câu
          </Label>
          <Label className="font-normal">
            <Checkbox checked={v.shuffle_options} onCheckedChange={(v) => set("shuffle_options", v === true)} /> Đảo phương án
          </Label>
        </div>
      </div>
      <div className="flex justify-end">
        <Button type="submit" disabled={m.busy || !v.class_ids.length}>
          Giao bài
        </Button>
      </div>
    </form>
  );
}
