"use client";

import { DateTimePicker } from "@/components/app/DatePicker";
import { FormAlert } from "@/components/app/FormAlert";
import { FormField } from "@/components/app/FormField";
import { OptionSelect } from "@/components/app/OptionSelect";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { RESULTS_POLICY_OPTIONS } from "@/constants/assignment.constant";
import { useAssignDialog } from "@/hooks/page-hooks/exam-detail/use-assign-dialog";
import type { Assignment } from "@/interfaces/assignment.interface";
import type { SchoolClass } from "@/interfaces/class.interface";
import type { ResultsPolicy } from "@/types/assignment.type";

export interface AssignDialogProps {
  examId: string;
  title: string;
  classes: SchoolClass[];
  onDone: (a: Assignment) => void;
}

export function AssignDialog({ examId, title, classes, onDone }: AssignDialogProps) {
  const a = useAssignDialog(examId, title, onDone);
  const { v, set, fields } = a;
  return (
    <form
      className="space-y-4"
      onSubmit={(e) => {
        e.preventDefault();
        a.submit();
      }}
    >
      {a.message && <FormAlert>{a.message}</FormAlert>}
      <FormField label="Tên bài" error={fields.title}>
        <Input value={v.title} onChange={(e) => set("title", e.target.value)} />
      </FormField>
      <FormField label="Lớp" error={fields.class_ids}>
        <div className="flex flex-wrap gap-2 text-sm" data-testid="class-options">
          {classes.map((c) => (
            <Label key={c.id} className="gap-1.5 rounded border border-border px-2 py-1 font-normal">
              <Checkbox checked={v.class_ids.includes(c.id)} onCheckedChange={(on) => a.toggleClass(c.id, on === true)} />
              {c.name} <span className="text-xs text-muted-foreground/70">({c.member_count})</span>
            </Label>
          ))}
        </div>
      </FormField>
      <div className="grid gap-3 sm:grid-cols-2">
        <FormField label="Mở lúc" error={fields.open_at}>
          {(f) => <DateTimePicker {...f} value={v.open_at} onChange={(x) => set("open_at", x)} />}
        </FormField>
        <FormField label="Đóng lúc" error={fields.close_at}>
          {(f) => <DateTimePicker {...f} value={v.close_at} onChange={(x) => set("close_at", x)} />}
        </FormField>
        <FormField label="Thời gian làm (phút)" error={fields.duration_minutes}>
          <Input type="number" min={1} max={600} value={v.duration_minutes} onChange={(e) => set("duration_minutes", Number(e.target.value))} />
        </FormField>
        <FormField label="Số lượt làm" error={fields.max_attempts}>
          <Input type="number" min={1} max={20} value={v.max_attempts} onChange={(e) => set("max_attempts", Number(e.target.value))} />
        </FormField>
        <FormField label="Xem kết quả">
          {(f) => <OptionSelect {...f} value={v.results_policy} onValueChange={(x) => set("results_policy", x as ResultsPolicy)} options={RESULTS_POLICY_OPTIONS} />}
        </FormField>
        <div className="space-y-1 pt-6 text-sm">
          <Label className="font-normal">
            <Checkbox checked={v.shuffle_questions} onCheckedChange={(on) => set("shuffle_questions", on === true)} /> Đảo thứ tự câu
          </Label>
          <Label className="font-normal">
            <Checkbox checked={v.shuffle_options} onCheckedChange={(on) => set("shuffle_options", on === true)} /> Đảo phương án
          </Label>
        </div>
      </div>
      <div className="flex justify-end">
        <Button type="submit" disabled={a.busy || !v.class_ids.length}>
          Giao bài
        </Button>
      </div>
    </form>
  );
}
