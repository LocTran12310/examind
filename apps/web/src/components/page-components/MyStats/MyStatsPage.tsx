"use client";

import { EmptyState } from "@/components/common/EmptyState/EmptyState";
import { GroupStats } from "@/components/common/GroupStats/GroupStats";
import { PageHeader } from "@/components/common/PageHeader/PageHeader";
import { Panel } from "@/components/common/Panel/Panel";
import { PracticeButton } from "@/components/common/PracticeButton/PracticeButton";
import { TopicStatsTree } from "@/components/common/TopicStatsTree/TopicStatsTree";
import { useMyStatsPage } from "@/hooks/page-hooks/my-stats/use-my-stats-page";
import { MasteryList } from "./MasteryList/MasteryList";
import { PracticeHistory } from "./PracticeHistory/PracticeHistory";

export function MyStatsPage() {
  const p = useMyStatsPage();
  if (!p.ready) return null;
  return (
    <>
      <PageHeader title="Tiến độ của tôi" description="Tỉ lệ làm đúng theo chuyên đề và loại câu" actions={p.canPractise ? <PracticeButton /> : undefined} />
      {p.topics.length === 0 ? (
        <EmptyState>Làm bài được giao để xem tiến độ của bạn.</EmptyState>
      ) : (
        <div className="space-y-4">
          <PracticeHistory items={p.practice} />
          <Panel>
            <h2 className="mb-2 font-medium">Mức nắm vững (cần ôn nhất trước)</h2>
            <MasteryList rows={p.mastery} limit={8} />
          </Panel>
          <Panel>
            <h2 className="mb-2 font-medium">Theo chuyên đề</h2>
            <TopicStatsTree rows={p.topics} />
          </Panel>
          <Panel>
            <h2 className="mb-2 font-medium">Theo loại câu</h2>
            <GroupStats by="type" rows={p.types} />
          </Panel>
        </div>
      )}
    </>
  );
}
