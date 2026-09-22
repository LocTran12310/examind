"use client";

import { DatePicker } from "@/components/common/DatePicker/DatePicker";
import { FormAlert } from "@/components/common/FormAlert/FormAlert";
import { FormField } from "@/components/common/FormField/FormField";
import { Button } from "@/components/ui/button";
import { DialogFooter } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { useYearForm } from "@/hooks/page-hooks/school-years/use-year-form";
import type { SchoolYear } from "@/interfaces/school-year.interface";

export interface YearFormProps {
  year?: SchoolYear;
  /** code proposed for a new year */
  suggest?: string;
  onDone: (y: SchoolYear) => void;
}

/** Create (code, default dates) or edit a year and its HK1/HK2 dates. */
export function YearForm({ year, suggest, onDone }: YearFormProps) {
  const m = useYearForm(year, suggest, onDone);
  const { v, setV, set } = m;
  return (
    <form
      className="grid gap-4"
      onSubmit={(e) => {
        e.preventDefault();
        m.submit();
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
