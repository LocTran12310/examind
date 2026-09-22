"use client";

import { MasteryList } from "@/components/adaptive/MasteryList";
import { PracticeButton, PracticeHistory } from "@/components/adaptive/PracticeButton";
import { GroupStats } from "@/components/reports/GroupStats";
import { TopicStatsTree } from "@/components/reports/TopicStatsTree";
import { Panel } from "@/components/app/Panel";
import { EmptyState } from "@/components/app/EmptyState";
import { PageHeader } from "@/components/app/PageHeader";
import { useApi } from "@/lib/hooks";
import type { GroupStat, MasteryRow, TopicStat } from "@/lib/types";

export default function MyStatsPage() {
  const { data: topics } = useApi<TopicStat[]>("/stats/topics");
  const { data: types } = useApi<GroupStat[]>("/stats/groups?by=type");
  const { data: mastery } = useApi<MasteryRow[]>("/me/mastery");
  if (!topics || !types || !mastery) return null;
  return (
    <>
      <PageHeader title="Tiến độ của tôi" description="Tỉ lệ làm đúng theo chuyên đề và loại câu" actions={<PracticeButton />} />
      {topics.length === 0 ? (
        <EmptyState>Làm bài được giao để xem tiến độ của bạn.</EmptyState>
      ) : (
        <div className="space-y-4">
          <PracticeHistory />
          <Panel>
            <h2 className="mb-2 font-medium">Mức nắm vững (cần ôn nhất trước)</h2>
            <MasteryList rows={mastery} limit={8} />
          </Panel>
          <Panel>
            <h2 className="mb-2 font-medium">Theo chuyên đề</h2>
            <TopicStatsTree rows={topics} />
          </Panel>
          <Panel>
            <h2 className="mb-2 font-medium">Theo loại câu</h2>
            <GroupStats by="type" rows={types} />
          </Panel>
        </div>
      )}
    </>
  );
}
