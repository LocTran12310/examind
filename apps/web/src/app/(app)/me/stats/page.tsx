"use client";

import { Bar } from "@/components/exams/ResultView";
import { GroupStats } from "@/components/reports/GroupStats";
import { TopicStatsTree, weakest } from "@/components/reports/TopicStatsTree";
import { Card, Empty, PageHeader } from "@/components/ui";
import { useApi } from "@/lib/hooks";
import type { GroupStat, TopicStat } from "@/lib/types";

export default function MyStatsPage() {
  const { data: topics } = useApi<TopicStat[]>("/stats/topics");
  const { data: types } = useApi<GroupStat[]>("/stats/groups?by=type");
  if (!topics || !types) return null;
  const weak = weakest(topics);
  return (
    <>
      <PageHeader title="Tiến độ của tôi" subtitle="Tỉ lệ làm đúng theo chuyên đề và loại câu" />
      {topics.length === 0 ? (
        <Empty>Làm bài được giao để xem tiến độ của bạn.</Empty>
      ) : (
        <div className="space-y-4">
          <Card>
            <h2 className="mb-2 font-medium">Cần ôn nhất</h2>
            <ul className="space-y-2" data-testid="weakest">
              {weak.map((t) => (
                <li key={t.path} className="grid grid-cols-[1fr_120px_48px] items-center gap-2 text-sm">
                  <span className="truncate">{t.name}</span>
                  <Bar ratio={t.ratio ?? 0} />
                  <span className="text-right">{Math.round((t.ratio ?? 0) * 100)}%</span>
                </li>
              ))}
            </ul>
          </Card>
          <Card>
            <h2 className="mb-2 font-medium">Theo chuyên đề</h2>
            <TopicStatsTree rows={topics} />
          </Card>
          <Card>
            <h2 className="mb-2 font-medium">Theo loại câu</h2>
            <GroupStats by="type" rows={types} />
          </Card>
        </div>
      )}
    </>
  );
}
