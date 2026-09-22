"use client";

import { useState } from "react";
import { FormAlert } from "@/components/app/FormAlert";
import { FormField } from "@/components/app/FormField";
import { OptionSelect } from "@/components/app/OptionSelect";
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

const GRADES = Array.from({ length: 12 }, (_, i) => ({ value: String(i + 1), label: `Khối ${i + 1}` }));

/** Create (no `klass`) or edit a class. */
export function ClassForm({ klass, onDone }: { klass?: SchoolClass; onDone: () => void }) {
  const [name, setName] = useState(klass?.name ?? "");
  const [grade, setGrade] = useState(klass?.grade ? String(klass.grade) : "");
  const [year, setYear] = useState(klass?.school_year ?? currentSchoolYear());
  const m = useMutation();
  return (
    <form
      className="grid gap-4"
      onSubmit={async (e) => {
        e.preventDefault();
        const body = { name, grade: grade ? Number(grade) : null, school_year: year };
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
          {(f) => <OptionSelect {...f} value={grade} onValueChange={setGrade} options={GRADES} emptyLabel="Không chọn" />}
        </FormField>
        <FormField label="Năm học" error={m.fields.school_year}>
          {(f) => <Input {...f} value={year} onChange={(e) => setYear(e.target.value)} />}
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
