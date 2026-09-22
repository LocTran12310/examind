"use client";

import { FormField } from "@/components/app/FormField";
import { Input } from "@/components/ui/input";
import { NativeSelect, NativeSelectOptGroup, NativeSelectOption } from "@/components/ui/native-select";
import { parsePeriod, periodOptions, periodValue } from "@/lib/exam-period";
import type { DocumentMeta, SchoolYear, Taxonomy } from "@/lib/types";

function groupBy<T extends { group: string }>(items: T[]): Record<string, T[]> {
  const out: Record<string, T[]> = {};
  for (const i of items) (out[i.group] ??= []).push(i);
  return out;
}

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
        <NativeSelect className="w-full" value={value.subject_id ?? ""} onChange={(e) => set("subject_id", e.target.value)}>
          <NativeSelectOption value="">{emptyLabel}</NativeSelectOption>
          {taxonomy.subjects.map((s) => (
            <NativeSelectOption key={s.id} value={s.id}>
              {s.name}
            </NativeSelectOption>
          ))}
        </NativeSelect>
      </FormField>
      <FormField label="Lớp" error={errors.grade}>
        <NativeSelect className="w-full" value={value.grade ?? ""} onChange={(e) => set("grade", e.target.value ? Number(e.target.value) : undefined)}>
          <NativeSelectOption value="">{emptyLabel}</NativeSelectOption>
          {taxonomy.grades.map((g) => (
            <NativeSelectOption key={g.id} value={g.level}>
              {g.name}
            </NativeSelectOption>
          ))}
        </NativeSelect>
      </FormField>
      <FormField label="Đợt kiểm tra" error={errors.semester_code ?? errors.exam_kind}>
        <NativeSelect className="w-full" value={periodValue(value.semester_code, value.exam_kind)} onChange={(e) => onChange({ ...value, ...parsePeriod(e.target.value) })}>
          <NativeSelectOption value="">{emptyLabel}</NativeSelectOption>
          {Object.entries(groupBy(periodOptions())).map(([group, opts]) => (
            <NativeSelectOptGroup key={group} label={group}>
              {opts.map((o) => (
                <NativeSelectOption key={o.value} value={o.value}>
                  {o.label}
                </NativeSelectOption>
              ))}
            </NativeSelectOptGroup>
          ))}
        </NativeSelect>
      </FormField>
      <FormField label="Năm học" error={errors.school_year}>
        {yearCodes.length ? (
          <NativeSelect className="w-full" value={value.school_year ?? ""} onChange={(e) => set("school_year", e.target.value)}>
            <NativeSelectOption value="">{emptyLabel}</NativeSelectOption>
            {yearCodes.map((c) => (
              <NativeSelectOption key={c} value={c}>
                {c}
              </NativeSelectOption>
            ))}
          </NativeSelect>
        ) : (
          <Input value={value.school_year ?? ""} placeholder="2024-2025" onChange={(e) => set("school_year", e.target.value)} />
        )}
      </FormField>
      <FormField label="Nguồn đề" error={errors.source_name} hint="Ví dụ: THPT Chu Văn An">
        <Input value={value.source_name ?? ""} placeholder={emptyLabel === "—" ? undefined : emptyLabel} onChange={(e) => set("source_name", e.target.value)} />
      </FormField>
    </div>
  );
}
