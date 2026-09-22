"use client";

import { Select, SelectContent, SelectGroup, SelectItem, SelectLabel, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useApi } from "@/lib/hooks";
import type { GradeRow, Page, SchoolLevel } from "@/lib/types";
import { cn } from "@/lib/utils";

const NONE = "__none";

/** Khối picker grouped by Cấp học (school-structure AC-06). Value is a grade id or "". */
export function GradeSelect({
  value,
  onValueChange,
  className,
  ...aria
}: {
  value: string;
  onValueChange: (gradeId: string, grade: GradeRow | undefined) => void;
  className?: string;
  id?: string;
  "aria-label"?: string;
  "aria-invalid"?: boolean;
  "aria-describedby"?: string;
}) {
  const { data: levels } = useApi<Page<SchoolLevel>>("/school-levels?page_size=all");
  const { data: grades } = useApi<Page<GradeRow>>("/grades?page_size=all");
  const all = grades?.items ?? [];
  const groups = (levels?.items ?? []).map((lv) => ({ lv, grades: all.filter((g) => g.school_level_id === lv.id) })).filter((x) => x.grades.length);
  const orphan = all.filter((g) => !g.school_level_id);
  return (
    <Select value={value || NONE} onValueChange={(v) => onValueChange(v === NONE ? "" : v, all.find((g) => g.id === v))}>
      <SelectTrigger className={cn("w-full", className)} {...aria}>
        <SelectValue placeholder="Chọn khối" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value={NONE}>Không chọn</SelectItem>
        {groups.map(({ lv, grades }) => (
          <SelectGroup key={lv.id}>
            <SelectLabel>{lv.name}</SelectLabel>
            {grades.map((g) => (
              <SelectItem key={g.id} value={g.id}>
                {g.name}
              </SelectItem>
            ))}
          </SelectGroup>
        ))}
        {orphan.length > 0 && (
          <SelectGroup>
            <SelectLabel>Chưa xếp cấp</SelectLabel>
            {orphan.map((g) => (
              <SelectItem key={g.id} value={g.id}>
                {g.name}
              </SelectItem>
            ))}
          </SelectGroup>
        )}
      </SelectContent>
    </Select>
  );
}
