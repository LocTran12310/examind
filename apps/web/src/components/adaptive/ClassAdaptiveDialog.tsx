"use client";

import { useState } from "react";
import { FormAlert } from "@/components/app/FormAlert";
import { Button } from "@/components/ui/button";
import { FormField } from "@/components/app/FormField";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";
import { fromLocalInput, toLocalInput } from "@/lib/dates";
import { useMutation } from "@/lib/hooks";

export function ClassAdaptiveDialog({ classId, onDone }: { classId: string; onDone: (created: number) => void }) {
  const [v, setV] = useState({ count: 15, duration_minutes: 30, open_at: toLocalInput(new Date()), close_at: toLocalInput(new Date(Date.now() + 3 * 86400_000)) });
  const m = useMutation();
  return (
    <form
      className="space-y-4"
      onSubmit={async (e) => {
        e.preventDefault();
        const r = await m.run(() =>
          api<{ created: number }>(`/classes/${classId}/adaptive-assignments`, {
            body: { ...v, open_at: fromLocalInput(v.open_at), close_at: fromLocalInput(v.close_at) },
          }),
        );
        if (r) onDone(r.created);
      }}
    >
      <p className="text-sm text-muted-foreground">Mỗi học sinh nhận một đề riêng, tập trung vào chuyên đề yếu của em và các câu từng làm sai.</p>
      {m.message && <FormAlert>{m.message}</FormAlert>}
      <div className="grid gap-3 sm:grid-cols-2">
        <FormField label="Số câu mỗi đề">
          <Input type="number" min={5} max={50} value={v.count} onChange={(e) => setV({ ...v, count: Number(e.target.value) })} />
        </FormField>
        <FormField label="Thời gian làm (phút)" error={m.fields.duration_minutes}>
          <Input type="number" min={1} max={600} value={v.duration_minutes} onChange={(e) => setV({ ...v, duration_minutes: Number(e.target.value) })} />
        </FormField>
        <FormField label="Mở lúc">
          <Input type="datetime-local" value={v.open_at} onChange={(e) => setV({ ...v, open_at: e.target.value })} />
        </FormField>
        <FormField label="Đóng lúc" error={m.fields.close_at}>
          <Input type="datetime-local" value={v.close_at} onChange={(e) => setV({ ...v, close_at: e.target.value })} />
        </FormField>
      </div>
      <div className="flex justify-end">
        <Button type="submit" disabled={m.busy}>
          Giao đề ôn cá nhân
        </Button>
      </div>
    </form>
  );
}
