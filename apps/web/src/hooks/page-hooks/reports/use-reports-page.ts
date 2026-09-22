import { useMemo, useState } from "react";
import { useYear } from "@/hooks/common/use-year";
import { useClassOptionsQuery } from "@/hooks/react-query/use-query-class";
import { useGroupStatsQuery, useHeatmapQuery, useTopicStatsQuery } from "@/hooks/react-query/use-query-stats";
import type { StatsParams } from "@/dtos/stats.dto";

export const REPORT_TABS = [
  ["topics", "Theo chuyên đề"],
  ["tag", "Theo tag"],
  ["type", "Theo loại câu"],
  ["difficulty", "Theo mức độ"],
  ["heatmap", "Bản đồ nhiệt lớp"],
] as const;
export type ReportTab = (typeof REPORT_TABS)[number][0];
const GROUP_TABS: readonly string[] = ["tag", "type", "difficulty"];

/** "Kết quả theo chuyên đề": the header year by default; a class narrows to that class (its own year) —
 *  school-years ADR-02; a term narrows further. One query per visible tab. */
export function useReportsPage() {
  const [tab, setTab] = useState<ReportTab>("topics");
  const [classId, setClassId] = useState("");
  const [level, setLevel] = useState("1");
  const [term, setTerm] = useState("");
  const { year } = useYear();
  const { data: classes } = useClassOptionsQuery(year?.id ?? null);
  const scope = useMemo<StatsParams>(
    () => ({ class_id: classId || undefined, school_year_id: classId ? undefined : year?.id, term_code: term || undefined }),
    [classId, year?.id, term],
  );
  const isGroup = GROUP_TABS.includes(tab);
  const { data: topics } = useTopicStatsQuery(scope, tab === "topics");
  const { data: groups } = useGroupStatsQuery(isGroup ? tab : "type", scope, isGroup);
  const { data: heat } = useHeatmapQuery(tab === "heatmap" && classId ? { class_id: classId, level, term_code: term || undefined } : null);
  const classOptions = useMemo(
    () =>
      [...(classes ?? [])]
        .sort((a, b) => (a.grade ?? 99) - (b.grade ?? 99) || a.name.localeCompare(b.name, "vi"))
        .map((c) => ({ value: c.id, label: `${c.name} (${c.school_year})`, group: c.grade ? `Khối ${c.grade}` : "Chưa xếp khối" })),
    [classes],
  );
  return { tab, setTab, isGroup, classId, setClassId, level, setLevel, term, setTerm, year, classOptions, topics, groups, heat };
}
