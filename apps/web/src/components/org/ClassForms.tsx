"use client";

import { useState } from "react";
import { Alert, Button, Field, Input } from "@/components/ui";
import { api } from "@/lib/api";
import { useMutation } from "@/lib/hooks";

export function currentSchoolYear(d = new Date()): string {
  const start = d.getMonth() >= 7 ? d.getFullYear() : d.getFullYear() - 1;
  return `${start}-${start + 1}`;
}

export function ClassCreateForm({ onCreated }: { onCreated: () => void }) {
  const [name, setName] = useState("");
  const [grade, setGrade] = useState("");
  const [year, setYear] = useState(currentSchoolYear());
  const m = useMutation();
  return (
    <form
      className="flex flex-wrap items-end gap-3"
      onSubmit={async (e) => {
        e.preventDefault();
        const r = await m.run(() => api("/classes", { body: { name, grade: grade ? Number(grade) : null, school_year: year } }));
        if (r) {
          setName("");
          setGrade("");
          onCreated();
        }
      }}
    >
      <div className="w-40">
        <Field label="Tên lớp" error={m.fields.name}>
          <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="10A1" required />
        </Field>
      </div>
      <div className="w-24">
        <Field label="Khối" error={m.fields.grade}>
          <Input value={grade} onChange={(e) => setGrade(e.target.value)} type="number" min={1} max={12} />
        </Field>
      </div>
      <div className="w-36">
        <Field label="Năm học" error={m.fields.school_year}>
          <Input value={year} onChange={(e) => setYear(e.target.value)} />
        </Field>
      </div>
      <Button variant="primary" type="submit" disabled={m.busy}>
        Tạo lớp
      </Button>
      {m.message && !Object.keys(m.fields).length && <Alert>{m.message}</Alert>}
    </form>
  );
}
