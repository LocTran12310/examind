"use client";

import { FormField } from "@/components/common/FormField/FormField";
import { Input } from "@/components/ui/input";
import { OptionSelect } from "@/components/common/OptionSelect/OptionSelect";
import { parsePeriod, periodOptions, periodValue } from "@/lib/common/exam-period";
import type { DocumentMeta } from "@/interfaces/document.interface";
import type { SchoolYear } from "@/interfaces/school-year.interface";
import type { Taxonomy } from "@/interfaces/taxonomy.interface";

/** Môn / Lớp / Đợt / Năm học / Nguồn đề. An empty field is filled from the exam header when the
 *  file is read (`emptyLabel`), so an official file needs no typing at all. */
export function DocumentMetaFields({
  value,
  onChange,
  taxonomy,
  years = [],
  errors = {},
  emptyLabel = "—",
}: {
  value: DocumentMeta;
  onChange: (m: DocumentMeta) => void;
  taxonomy: Taxonomy;
  years?: Pick<SchoolYear, "id" | "code">[];
  errors?: Record<string, string>;
  emptyLabel?: string;
}) {
  const set = (k: keyof DocumentMeta, v: string | number | undefined) => onChange({ ...value, [k]: v === "" ? undefined : v });
  const yearCodes = [...new Set([...years.map((y) => y.code), ...(value.school_year ? [value.school_year] : [])])].sort().reverse();
  return (
    <div className="grid gap-3 sm:grid-cols-3">
      <FormField label="Môn" error={errors.subject_id}>
        {(f) => (
          <OptionSelect
            {...f}
            value={value.subject_id ?? ""}
            onValueChange={(v) => set("subject_id", v)}
            emptyLabel={emptyLabel}
            options={taxonomy.subjects.map((s) => ({ value: s.id, label: s.name }))}
          />
        )}
      </FormField>
      <FormField label="Lớp" error={errors.grade}>
        {(f) => (
          <OptionSelect
            {...f}
            value={value.grade != null ? String(value.grade) : ""}
            onValueChange={(v) => set("grade", v ? Number(v) : undefined)}
            emptyLabel={emptyLabel}
            options={taxonomy.grades.map((g) => ({ value: String(g.level), label: g.name }))}
          />
        )}
      </FormField>
      <FormField label="Đợt kiểm tra" error={errors.semester_code ?? errors.exam_kind}>
        {(f) => (
          <OptionSelect
            {...f}
            value={periodValue(value.semester_code, value.exam_kind)}
            onValueChange={(v) => onChange({ ...value, ...parsePeriod(v) })}
            emptyLabel={emptyLabel}
            options={periodOptions()}
          />
        )}
      </FormField>
      <FormField label="Năm học" error={errors.school_year}>
        {(f) =>
          yearCodes.length ? (
            <OptionSelect {...f} value={value.school_year ?? ""} onValueChange={(v) => set("school_year", v)} emptyLabel={emptyLabel} options={yearCodes.map((c) => ({ value: c, label: c }))} />
          ) : (
            <Input {...f} value={value.school_year ?? ""} placeholder="2024-2025" onChange={(e) => set("school_year", e.target.value)} />
          )
        }
      </FormField>
      <FormField label="Nguồn đề" error={errors.source_name} hint="Ví dụ: THPT Chu Văn An">
        <Input value={value.source_name ?? ""} placeholder={emptyLabel === "—" ? undefined : emptyLabel} onChange={(e) => set("source_name", e.target.value)} />
      </FormField>
    </div>
  );
}
