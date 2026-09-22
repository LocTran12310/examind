"use client";

import { GroupStats } from "@/components/common/GroupStats/GroupStats";
import { OptionSelect } from "@/components/common/OptionSelect/OptionSelect";
import { PageHeader } from "@/components/common/PageHeader/PageHeader";
import { Panel } from "@/components/common/Panel/Panel";
import { TopicStatsTree } from "@/components/common/TopicStatsTree/TopicStatsTree";
import { Button } from "@/components/ui/button";
import { REPORT_TABS, useReportsPage } from "@/hooks/page-hooks/reports/use-reports-page";
import { cn } from "@/lib/utils";
import { Heatmap } from "./Heatmap/Heatmap";

export function ReportsPage() {
  const p = useReportsPage();
  return (
    <>
      <PageHeader title="Kết quả theo chuyên đề" description={`Tỉ lệ đúng cộng dồn từ các nhánh con lên cấp trên${p.year ? " · " + p.year.name : ""}`} />
      <div className="mb-4 flex flex-wrap items-center gap-2">
        <OptionSelect aria-label="Học kỳ" className="w-36" value={p.term} onValueChange={p.setTerm} emptyLabel="Cả năm" options={[{ value: "hk1", label: "Học kỳ 1" }, { value: "hk2", label: "Học kỳ 2" }]} />
        <OptionSelect aria-label="Lớp" className="w-56" value={p.classId} onValueChange={p.setClassId} emptyLabel="Cả trung tâm" options={p.classOptions} />
        <div className="flex flex-wrap gap-1" role="tablist">
          {REPORT_TABS.map(([k, label]) => (
            <Button
              key={k}
              type="button"
              variant="ghost"
              role="tab"
              aria-selected={p.tab === k}
              onClick={() => p.setTab(k)}
              className={cn("font-normal", p.tab === k ? "bg-primary/10 font-medium text-primary hover:bg-primary/10 hover:text-primary" : "text-muted-foreground")}
            >
              {label}
            </Button>
          ))}
        </div>
      </div>
      <Panel>
        {p.tab === "topics" && p.topics && <TopicStatsTree rows={p.topics} />}
        {p.isGroup && p.groups && <GroupStats by={p.tab} rows={p.groups} />}
        {p.tab === "heatmap" && (
          <>
            <div className="mb-3 flex items-center gap-2 text-sm">
              Cấp chuyên đề
              <OptionSelect
                aria-label="Cấp"
                className="w-44"
                value={p.level}
                onValueChange={p.setLevel}
                options={[
                  { value: "1", label: "Mạch kiến thức" },
                  { value: "2", label: "Chuyên đề" },
                  { value: "3", label: "Chủ đề con" },
                ]}
              />
            </div>
            {!p.classId ? <p className="text-sm text-muted-foreground">Chọn một lớp để xem bản đồ nhiệt.</p> : p.heat && <Heatmap data={p.heat} />}
          </>
        )}
      </Panel>
    </>
  );
}
