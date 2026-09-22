"use client";

import { FormAlert } from "@/components/app/FormAlert";
import { FormField } from "@/components/app/FormField";
import { Button } from "@/components/ui/button";
import { DialogFooter } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { useGradeForm } from "@/hooks/page-hooks/structure/use-structure-forms";
import type { GradeRow } from "@/interfaces/structure.interface";

export interface GradeFormProps {
  grade?: GradeRow;
  levelId: string;
  onDone: () => void;
}

export function GradeForm({ grade, levelId, onDone }: GradeFormProps) {
  const m = useGradeForm(grade, levelId, onDone);
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
        <FormField label="Khối" error={m.fields.level}>
          <Input type="number" min={1} max={12} value={m.level} onChange={(e) => m.setLevel(e.target.value)} required />
        </FormField>
        <FormField label="Tên hiển thị" hint="Để trống: “Lớp N”" error={m.fields.name}>
          <Input value={m.name} onChange={(e) => m.setName(e.target.value)} />
        </FormField>
      </div>
      <DialogFooter>
        <Button type="submit" disabled={m.busy}>
          {grade ? "Lưu" : "Thêm khối"}
        </Button>
      </DialogFooter>
    </form>
  );
}
