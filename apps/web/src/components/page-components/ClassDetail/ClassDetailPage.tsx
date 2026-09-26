"use client";

import { BackLink } from "@/components/common/BackLink/BackLink";
import { FormAlert } from "@/components/common/FormAlert/FormAlert";
import { FormDialog } from "@/components/common/FormDialog/FormDialog";
import { PageHeader } from "@/components/common/PageHeader/PageHeader";
import { Panel } from "@/components/common/Panel/Panel";
import { MemberManager } from "@/components/page-components/Classes/MemberManager/MemberManager";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useClassDetailPage } from "@/hooks/page-hooks/class-detail/use-class-detail-page";
import { ClassAdaptiveDialog } from "./ClassAdaptiveDialog/ClassAdaptiveDialog";
import { ClassOverview } from "./ClassOverview/ClassOverview";
import { ClassSummary } from "./ClassSummary/ClassSummary";

export function ClassDetailPage({ id }: { id: string }) {
  const p = useClassDetailPage(id);
  if (p.error) return <p className="text-sm text-destructive">{p.error}</p>;
  if (!p.data) return null;
  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <BackLink href="/org/classes">Lớp học</BackLink>
      <PageHeader
        title={`Lớp ${p.data.name}`}
        description={`${p.data.school_year} · ${p.data.member_count} học sinh`}
        actions={<Button variant="outline" onClick={() => p.setAdaptive(true)}>Giao đề ôn cá nhân</Button>}
      />
      {p.notice && <div className="mb-4"><FormAlert kind="success">{p.notice}</FormAlert></div>}
      <FormDialog open={p.adaptive} title="Giao đề ôn cá nhân cho cả lớp" onOpenChange={(o) => !o && p.setAdaptive(false)}>
        <ClassAdaptiveDialog classId={id} onDone={p.assigned} />
      </FormDialog>
      {/* a column that fills the page: the overview scrolls as a whole, while the students tab hands its height
          to the table so that table keeps its own toolbar, header and pagination still (MasterDetail says the
          same thing about detail panes) */}
      <Tabs defaultValue="overview" className="flex min-h-0 flex-1 flex-col">
        <TabsList aria-label="Xem lớp" className="mb-4">
          <TabsTrigger value="overview">Tổng quan</TabsTrigger>
          <TabsTrigger value="students">Học sinh</TabsTrigger>
        </TabsList>
        {/* AC-03: cả lớp trước, từng em sau — người dạy hỏi "lớp thế nào" trước khi hỏi "em nào" */}
        <TabsContent value="overview" className="min-h-0 flex-1 overflow-auto">
          {p.summary && <ClassSummary data={p.summary} />}
          {p.overview && p.overview.length > 0 && (
            <Panel className="mt-4">
              <h2 className="mb-3 font-medium">Tình hình học tập</h2>
              <ClassOverview rows={p.overview} />
            </Panel>
          )}
        </TabsContent>
        <TabsContent value="students" className="min-h-0 flex-1">
          <MemberManager classId={id} />
        </TabsContent>
      </Tabs>
    </div>
  );
}
