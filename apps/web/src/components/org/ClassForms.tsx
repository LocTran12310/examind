"use client";

import { useState } from "react";
import { FormAlert } from "@/components/app/FormAlert";
import { FormField } from "@/components/app/FormField";
import { OptionSelect } from "@/components/app/OptionSelect";
import { useYear } from "@/components/app/YearContext";
import { GradeSelect } from "@/components/structure/GradeSelect";
import { Button } from "@/components/ui/button";
import { DialogFooter } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";
import { useMutation } from "@/lib/hooks";
import type { SchoolClass } from "@/lib/types";

export function currentSchoolYear(d = new Date()): string {
  const start = d.getMonth() >= 7 ? d.getFullYear() : d.getFullYear() - 1;
  return `${start}-${start + 1}`;
}

/** Create (no `klass`) or edit a class; `gradeId` preselects the khối (structure page). */
export function ClassForm({ klass, gradeId, onDone }: { klass?: SchoolClass; gradeId?: string; onDone: () => void }) {
  const [name, setName] = useState(klass?.name ?? "");
  const [grade, setGrade] = useState(klass?.grade_id ?? gradeId ?? "");
  const { years, year: selected } = useYear();
  const [yearId, setYearId] = useState(klass?.school_year_id ?? selected?.id ?? "");
  const m = useMutation();
  return (
    <form
      className="grid gap-4"
      onSubmit={async (e) => {
        e.preventDefault();
        const body = yearId ? { name, grade_id: grade || null, school_year_id: yearId } : { name, grade_id: grade || null, school_year: currentSchoolYear() };
        const r = await m.run(() => (klass ? api(`/classes/${klass.id}`, { method: "PATCH", body }) : api("/classes", { body })));
        if (r) onDone();
      }}
    >
      {m.message && !Object.keys(m.fields).length && <FormAlert>{m.message}</FormAlert>}
      <FormField label="Tên lớp" error={m.fields.name}>
        {(f) => <Input {...f} value={name} onChange={(e) => setName(e.target.value)} placeholder="10A1" required />}
      </FormField>
      <div className="grid grid-cols-2 gap-4">
        <FormField label="Khối" error={m.fields.grade}>
          {(f) => <GradeSelect {...f} value={grade} onValueChange={(v) => setGrade(v)} />}
        </FormField>
        <FormField label="Năm học" error={m.fields.school_year ?? m.fields.school_year_id}>
          {(f) =>
            years.length ? (
              <OptionSelect {...f} value={yearId} onValueChange={setYearId} options={years.map((y) => ({ value: y.id, label: y.code }))} />
            ) : (
              <Input {...f} value={currentSchoolYear()} disabled />
            )
          }
        </FormField>
      </div>
      <DialogFooter>
        <Button type="submit" disabled={m.busy}>
          {klass ? "Lưu" : "Tạo lớp"}
        </Button>
      </DialogFooter>
    </form>
  );
}
