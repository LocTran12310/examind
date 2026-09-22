"use client";

import { useState } from "react";
import { FormAlert } from "@/components/app/FormAlert";
import { FormField } from "@/components/app/FormField";
import { Button } from "@/components/ui/button";
import { DialogFooter } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";
import { useMutation } from "@/lib/hooks";
import type { GradeRow, SchoolLevel } from "@/lib/types";

export function LevelForm({ level, onDone }: { level?: SchoolLevel; onDone: () => void }) {
  const [v, setV] = useState({ code: level?.code ?? "", name: level?.name ?? "", grade_from: String(level?.grade_from ?? ""), grade_to: String(level?.grade_to ?? "") });
  const m = useMutation();
  const set = (k: keyof typeof v) => (e: React.ChangeEvent<HTMLInputElement>) => setV({ ...v, [k]: e.target.value });
  return (
    <form
      className="grid gap-4"
      onSubmit={async (e) => {
        e.preventDefault();
        const body = { code: v.code, name: v.name, grade_from: Number(v.grade_from), grade_to: Number(v.grade_to) };
        const r = await m.run(() => (level ? api(`/school-levels/${level.id}`, { method: "PATCH", body }) : api("/school-levels", { body })));
        if (r) onDone();
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

export function GradeForm({ grade, levelId, onDone }: { grade?: GradeRow; levelId: string; onDone: () => void }) {
  const [level, setLevel] = useState(String(grade?.level ?? ""));
  const [name, setName] = useState(grade?.name ?? "");
  const m = useMutation();
  return (
    <form
      className="grid gap-4"
      onSubmit={async (e) => {
        e.preventDefault();
        const body = { level: Number(level), name: name || null, school_level_id: levelId };
        const r = await m.run(() => (grade ? api(`/grades/${grade.id}`, { method: "PATCH", body }) : api("/grades", { body })));
        if (r) onDone();
      }}
    >
      {m.message && !Object.keys(m.fields).length && <FormAlert>{m.message}</FormAlert>}
      <div className="grid grid-cols-[8rem_1fr] gap-4">
        <FormField label="Khối" error={m.fields.level}>
          <Input type="number" min={1} max={12} value={level} onChange={(e) => setLevel(e.target.value)} required />
        </FormField>
        <FormField label="Tên hiển thị" hint="Để trống: “Lớp N”" error={m.fields.name}>
          <Input value={name} onChange={(e) => setName(e.target.value)} />
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
