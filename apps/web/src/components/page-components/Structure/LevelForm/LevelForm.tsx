"use client";

import { FormAlert } from "@/components/app/FormAlert";
import { FormField } from "@/components/app/FormField";
import { Button } from "@/components/ui/button";
import { DialogFooter } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { useLevelForm } from "@/hooks/page-hooks/structure/use-structure-forms";
import type { SchoolLevel } from "@/interfaces/structure.interface";

export interface LevelFormProps {
  level?: SchoolLevel;
  onDone: () => void;
}

export function LevelForm({ level, onDone }: LevelFormProps) {
  const m = useLevelForm(level, onDone);
  const { v, set } = m;
  return (
    <form
      className="grid gap-4"
      onSubmit={(e) => {
        e.preventDefault();
        m.submit();
      }}
    >
      {m.message && !Object.keys(m.fields).length && <FormAlert>{m.message}</FormAlert>}
      <div className="grid grid-cols-[8rem_1fr] gap-4">
        <FormField label="Mã" error={m.fields.code}>
          <Input value={v.code} onChange={set("code")} placeholder="thpt" required />
        </FormField>
        <FormField label="Tên cấp học" error={m.fields.name}>
          <Input value={v.name} onChange={set("name")} placeholder="Trung học phổ thông" required />
        </FormField>
      </div>
      <div className="grid grid-cols-2 gap-4">
        <FormField label="Từ khối" error={m.fields.grade_from}>
          <Input type="number" min={1} max={12} value={v.grade_from} onChange={set("grade_from")} required />
        </FormField>
        <FormField label="Đến khối" error={m.fields.grade_to}>
          <Input type="number" min={1} max={12} value={v.grade_to} onChange={set("grade_to")} required />
        </FormField>
      </div>
      <DialogFooter>
        <Button type="submit" disabled={m.busy}>
          {level ? "Lưu" : "Thêm cấp học"}
        </Button>
      </DialogFooter>
    </form>
  );
}
