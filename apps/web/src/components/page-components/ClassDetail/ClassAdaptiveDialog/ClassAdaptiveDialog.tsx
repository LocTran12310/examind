"use client";

import { DateTimePicker } from "@/components/common/DatePicker/DatePicker";
import { FormAlert } from "@/components/common/FormAlert/FormAlert";
import { FormField } from "@/components/common/FormField/FormField";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useClassAdaptiveDialog } from "@/hooks/page-hooks/class-detail/use-class-adaptive-dialog";

export function ClassAdaptiveDialog({ classId, onDone }: { classId: string; onDone: (created: number) => void }) {
  const { v, setV, fields, message, busy, submit } = useClassAdaptiveDialog(classId, onDone);
  return (
    <form
      className="space-y-4"
      onSubmit={(e) => {
        e.preventDefault();
        submit();
      }}
    >
      <p className="text-sm text-muted-foreground">Mỗi học sinh nhận một đề riêng, tập trung vào chuyên đề yếu của em và các câu từng làm sai.</p>
      {message && <FormAlert>{message}</FormAlert>}
      <div className="grid gap-3 sm:grid-cols-2">
        <FormField label="Số câu mỗi đề">
          <Input type="number" min={5} max={50} value={v.count} onChange={(e) => setV({ ...v, count: Number(e.target.value) })} />
        </FormField>
        <FormField label="Thời gian làm (phút)" error={fields.duration_minutes}>
          <Input type="number" min={1} max={600} value={v.duration_minutes} onChange={(e) => setV({ ...v, duration_minutes: Number(e.target.value) })} />
        </FormField>
        <FormField label="Mở lúc">
          {(f) => <DateTimePicker {...f} value={v.open_at} onChange={(x) => setV({ ...v, open_at: x })} />}
        </FormField>
        <FormField label="Đóng lúc" error={fields.close_at}>
          {(f) => <DateTimePicker {...f} value={v.close_at} onChange={(x) => setV({ ...v, close_at: x })} />}
        </FormField>
      </div>
      <div className="flex justify-end">
        <Button type="submit" disabled={busy}>
          Giao đề ôn cá nhân
        </Button>
      </div>
    </form>
  );
}
