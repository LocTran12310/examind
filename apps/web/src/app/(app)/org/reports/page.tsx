"use client";

import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { useState } from "react";
import { GroupStats } from "@/components/reports/GroupStats";
import { Heatmap, type HeatmapData } from "@/components/reports/Heatmap";
import { TopicStatsTree } from "@/components/reports/TopicStatsTree";
import { Panel } from "@/components/app/Panel";
import { PageHeader } from "@/components/app/PageHeader";
import { OptionSelect } from "@/components/app/OptionSelect";
import { useYear } from "@/components/app/YearContext";
import { NativeSelect, NativeSelectOption } from "@/components/ui/native-select";
import { qs, useApi } from "@/lib/hooks";
import type { GroupStat, SchoolClass, TopicStat, Page } from "@/lib/types";

const TABS = [
  ["topics", "Theo chuyên đề"],
  ["tag", "Theo tag"],
  ["type", "Theo loại câu"],
  ["difficulty", "Theo mức độ"],
  ["heatmap", "Bản đồ nhiệt lớp"],
] as const;

export default function ReportsPage() {
  const [tab, setTab] = useState<(typeof TABS)[number][0]>("topics");
  const [classId, setClassId] = useState("");
  const [level, setLevel] = useState("1");
  const [term, setTerm] = useState("");
  const { year } = useYear();
  // whole year by default; picking a class narrows to that class (its own year) — school-years ADR-02
  const { data: classesPage } = useApi<Page<SchoolClass>>(`/classes?page_size=all${year ? `&school_year_id=${year.id}` : ""}`);
  const classes = classesPage?.items;
  const scopeParams = { class_id: classId, school_year_id: classId ? undefined : year?.id, term_code: term };
  const filters = qs(scopeParams);
  const { data: topics } = useApi<TopicStat[]>(tab === "topics" ? `/stats/topics${filters}` : null);
  const { data: groups } = useApi<GroupStat[]>(["tag", "type", "difficulty"].includes(tab) ? `/stats/groups${qs({ by: tab, ...scopeParams })}` : null);
  const { data: heat } = useApi<HeatmapData>(tab === "heatmap" && classId ? `/stats/heatmap${qs({ class_id: classId, level, term_code: term })}` : null);

  return (
    <>
      <PageHeader title="Kết quả theo chuyên đề" description={`Tỉ lệ đúng cộng dồn từ các nhánh con lên cấp trên${year ? " · " + year.name : ""}`} />
      <div className="mb-4 flex flex-wrap items-center gap-2">
        <OptionSelect aria-label="Học kỳ" className="w-36" value={term} onValueChange={setTerm} emptyLabel="Cả năm" options={[{ value: "hk1", label: "Học kỳ 1" }, { value: "hk2", label: "Học kỳ 2" }]} />
        <OptionSelect
          aria-label="Lớp"
          className="w-56"
          value={classId}
          onValueChange={setClassId}
          emptyLabel="Cả trung tâm"
          options={[...(classes ?? [])]
            .sort((a, b) => (a.grade ?? 99) - (b.grade ?? 99) || a.name.localeCompare(b.name, "vi"))
            .map((c) => ({ value: c.id, label: `${c.name} (${c.school_year})`, group: c.grade ? `Khối ${c.grade}` : "Chưa xếp khối" }))}
        />
        <div className="flex flex-wrap gap-1" role="tablist">
          {TABS.map(([k, label]) => (
            <Button
              key={k}
              type="button"
              variant="ghost"
              role="tab"
              aria-selected={tab === k}
              onClick={() => setTab(k)}
              className={cn("font-normal", tab === k ? "bg-primary/10 font-medium text-primary hover:bg-primary/10 hover:text-primary" : "text-muted-foreground")}
            >
              {label}
            </Button>
          ))}
        </div>
      </div>
      <Panel>
        {tab === "topics" && topics && <TopicStatsTree rows={topics} />}
        {["tag", "type", "difficulty"].includes(tab) && groups && <GroupStats by={tab} rows={groups} />}
        {tab === "heatmap" && (
          <>
            <div className="mb-3 flex items-center gap-2 text-sm">
              Cấp chuyên đề
              <NativeSelect aria-label="Cấp" value={level} onChange={(e) => setLevel(e.target.value)}>
                <NativeSelectOption value="1">Mạch kiến thức</NativeSelectOption>
                <NativeSelectOption value="2">Chuyên đề</NativeSelectOption>
                <NativeSelectOption value="3">Chủ đề con</NativeSelectOption>
              </NativeSelect>
            </div>
            {!classId ? <p className="text-sm text-muted-foreground">Chọn một lớp để xem bản đồ nhiệt.</p> : heat && <Heatmap data={heat} />}
          </>
        )}
      </Panel>
    </>
  );
}
