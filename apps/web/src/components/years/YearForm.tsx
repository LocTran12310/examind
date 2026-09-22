"use client";

import { useState } from "react";
import { FormAlert } from "@/components/app/FormAlert";
import { FormField } from "@/components/app/FormField";
import { Button } from "@/components/ui/button";
import { DialogFooter } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";
import { useMutation } from "@/lib/hooks";
import type { SchoolYear } from "@/lib/types";
import { DatePicker } from "@/components/app/DatePicker";

export function nextYearCode(code?: string): string {
  const y = code ? Number(code.slice(5)) : new Date().getFullYear();
  return `${y}-${y + 1}`;
}

/** Create (code, default dates) or edit a year and its HK1/HK2 dates. */
export function YearForm({ year, suggest, onDone }: { year?: SchoolYear; suggest?: string; onDone: (y: SchoolYear) => void }) {
  const t = (c: string) => year?.terms.find((x) => x.code === c);
  const [v, setV] = useState({
    code: year?.code ?? suggest ?? "",
    name: year?.name ?? "",
    start_date: year?.start_date ?? "",
    end_date: year?.end_date ?? "",
    hk1_start: t("hk1")?.start_date ?? "",
    hk1_end: t("hk1")?.end_date ?? "",
    hk2_start: t("hk2")?.start_date ?? "",
    hk2_end: t("hk2")?.end_date ?? "",
  });
  const m = useMutation();
  const set = (k: keyof typeof v) => (e: React.ChangeEvent<HTMLInputElement>) => setV({ ...v, [k]: e.target.value });
  return (
    <form
      className="grid gap-4"
      onSubmit={async (e) => {
        e.preventDefault();
        const terms =
          v.hk1_start && v.hk1_end && v.hk2_start && v.hk2_end
            ? [
                { code: "hk1", start_date: v.hk1_start, end_date: v.hk1_end },
                { code: "hk2", start_date: v.hk2_start, end_date: v.hk2_end },
              ]
            : undefined;
        const body = { name: v.name || null, start_date: v.start_date || null, end_date: v.end_date || null, terms };
        const r = await m.run(() =>
          year ? api<SchoolYear>(`/school-years/${year.id}`, { method: "PATCH", body }) : api<SchoolYear>("/school-years", { body: { ...body, code: v.code } }),
        );
        if (r) onDone(r);
      }}
    >
      {m.message && !Object.keys(m.fields).length && <FormAlert>{m.message}</FormAlert>}
      <div className="grid grid-cols-[9rem_1fr] gap-4">
        <FormField label="Năm học" error={m.fields.code}>
          <Input value={v.code} onChange={set("code")} placeholder="2027-2028" disabled={!!year} required />
        </FormField>
        <FormField label="Tên hiển thị" hint="Để trống: “Năm học 2027-2028”" error={m.fields.name}>
          <Input value={v.name} onChange={set("name")} />
        </FormField>
      </div>
      {year && (
        <>
          <div className="grid grid-cols-2 gap-4">
            <FormField label="Bắt đầu" error={m.fields.start_date}>
              {(f) => <DatePicker {...f} clearable={false} value={v.start_date} onChange={(d) => setV({ ...v, start_date: d })} />}
            </FormField>
            <FormField label="Kết thúc" error={m.fields.end_date}>
              {(f) => <DatePicker {...f} clearable={false} value={v.end_date} onChange={(d) => setV({ ...v, end_date: d })} />}
            </FormField>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <FormField label="Học kỳ 1 từ" error={m.fields.terms}>
              {(f) => <DatePicker {...f} clearable={false} value={v.hk1_start} onChange={(d) => setV({ ...v, hk1_start: d })} />}
            </FormField>
            <FormField label="đến">
              {(f) => <DatePicker {...f} clearable={false} value={v.hk1_end} onChange={(d) => setV({ ...v, hk1_end: d })} />}
            </FormField>
            <FormField label="Học kỳ 2 từ">
              {(f) => <DatePicker {...f} clearable={false} value={v.hk2_start} onChange={(d) => setV({ ...v, hk2_start: d })} />}
            </FormField>
            <FormField label="đến">
              {(f) => <DatePicker {...f} clearable={false} value={v.hk2_end} onChange={(d) => setV({ ...v, hk2_end: d })} />}
            </FormField>
          </div>
        </>
      )}
      {!year && <p className="text-sm text-muted-foreground">Ngày mặc định 05/09 – 31/05, HK1 đến 15/01. Sửa sau khi tạo nếu cần.</p>}
      <DialogFooter>
        <Button type="submit" disabled={m.busy}>
          {year ? "Lưu" : "Tạo năm học"}
        </Button>
      </DialogFooter>
    </form>
  );
}
