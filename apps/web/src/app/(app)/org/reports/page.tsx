"use client";

import clsx from "clsx";
import { useState } from "react";
import { GroupStats } from "@/components/reports/GroupStats";
import { Heatmap, type HeatmapData } from "@/components/reports/Heatmap";
import { TopicStatsTree } from "@/components/reports/TopicStatsTree";
import { Card, PageHeader, Select } from "@/components/ui";
import { qs, useApi } from "@/lib/hooks";
import type { GroupStat, SchoolClass, TopicStat } from "@/lib/types";

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
  const { data: classes } = useApi<SchoolClass[]>("/classes");
  const filters = qs({ class_id: classId });
  const { data: topics } = useApi<TopicStat[]>(tab === "topics" ? `/stats/topics${filters}` : null);
  const { data: groups } = useApi<GroupStat[]>(["tag", "type", "difficulty"].includes(tab) ? `/stats/groups${qs({ by: tab, class_id: classId })}` : null);
  const { data: heat } = useApi<HeatmapData>(tab === "heatmap" && classId ? `/stats/heatmap${qs({ class_id: classId, level })}` : null);

  return (
    <>
      <PageHeader title="Kết quả theo chuyên đề" subtitle="Tỉ lệ đúng cộng dồn từ các nhánh con lên cấp trên" />
      <div className="mb-4 flex flex-wrap items-center gap-2">
        <Select aria-label="Lớp" value={classId} onChange={(e) => setClassId(e.target.value)}>
          <option value="">Toàn trung tâm</option>
          {classes?.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))}
        </Select>
        <div className="flex flex-wrap gap-1" role="tablist">
          {TABS.map(([k, label]) => (
            <button
              key={k}
              role="tab"
              aria-selected={tab === k}
              onClick={() => setTab(k)}
              className={clsx("rounded-md px-3 py-1.5 text-sm", tab === k ? "bg-brand-50 font-medium text-brand-700" : "text-gray-600 hover:bg-gray-100")}
            >
              {label}
            </button>
          ))}
        </div>
      </div>
      <Card>
        {tab === "topics" && topics && <TopicStatsTree rows={topics} />}
        {["tag", "type", "difficulty"].includes(tab) && groups && <GroupStats by={tab} rows={groups} />}
        {tab === "heatmap" && (
          <>
            <div className="mb-3 flex items-center gap-2 text-sm">
              Cấp chuyên đề
              <Select aria-label="Cấp" value={level} onChange={(e) => setLevel(e.target.value)}>
                <option value="1">Mạch kiến thức</option>
                <option value="2">Chuyên đề</option>
                <option value="3">Chủ đề con</option>
              </Select>
            </div>
            {!classId ? <p className="text-sm text-gray-500">Chọn một lớp để xem bản đồ nhiệt.</p> : heat && <Heatmap data={heat} />}
          </>
        )}
      </Card>
    </>
  );
}
