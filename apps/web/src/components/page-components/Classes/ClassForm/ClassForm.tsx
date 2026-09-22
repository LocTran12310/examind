"use client";

import { FormAlert } from "@/components/app/FormAlert";
import { FormField } from "@/components/app/FormField";
import { OptionSelect } from "@/components/app/OptionSelect";
import { Button } from "@/components/ui/button";
import { DialogFooter } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { useClassForm } from "@/hooks/page-hooks/classes/use-class-form";
import type { SchoolClass } from "@/interfaces/class.interface";
import { GradeSelect } from "../GradeSelect/GradeSelect";

export interface ClassFormProps {
  klass?: SchoolClass;
  /** preselects the khối (structure page) */
  gradeId?: string;
  onDone: () => void;
}

/** Create (no `klass`) or edit a class. */
export function ClassForm({ klass, gradeId, onDone }: ClassFormProps) {
  const f = useClassForm(klass, gradeId, onDone);
  return (
    <form
      className="grid gap-4"
      onSubmit={(e) => {
        e.preventDefault();
        f.submit();
      }}
    >
      {f.message && !Object.keys(f.fields).length && <FormAlert>{f.message}</FormAlert>}
      <FormField label="Tên lớp" error={f.fields.name}>
        {(p) => <Input {...p} value={f.name} onChange={(e) => f.setName(e.target.value)} placeholder="10A1" required />}
      </FormField>
      <div className="grid grid-cols-2 gap-4">
        <FormField label="Khối" error={f.fields.grade}>
          {(p) => <GradeSelect {...p} value={f.grade} onValueChange={(v) => f.setGrade(v)} />}
        </FormField>
        <FormField label="Năm học" error={f.fields.school_year ?? f.fields.school_year_id}>
          {(p) =>
            f.yearOptions.length ? (
              <OptionSelect {...p} value={f.yearId} onValueChange={f.setYearId} options={f.yearOptions} />
            ) : (
              <Input {...p} value={f.fallbackYear} disabled />
            )
          }
        </FormField>
      </div>
      <DialogFooter>
        <Button type="submit" disabled={f.busy}>
          {klass ? "Lưu" : "Tạo lớp"}
        </Button>
      </DialogFooter>
    </form>
  );
}
