"use client";

import { ClassAdaptiveDialog } from "@/components/adaptive/ClassAdaptiveDialog";
import { ClassOverview } from "@/components/adaptive/ClassOverview";
import { BackLink } from "@/components/app/BackLink";
import { FormAlert } from "@/components/app/FormAlert";
import { FormDialog } from "@/components/app/FormDialog";
import { PageHeader } from "@/components/app/PageHeader";
import { Panel } from "@/components/app/Panel";
import { MemberManager } from "@/components/page-components/Classes/MemberManager/MemberManager";
import { Button } from "@/components/ui/button";
import { useClassDetailPage } from "@/hooks/page-hooks/class-detail/use-class-detail-page";

export function ClassDetailPage({ id }: { id: string }) {
  const p = useClassDetailPage(id);
  if (p.error) return <p className="text-sm text-destructive">{p.error}</p>;
  if (!p.data) return null;
  return (
    <>
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
      {p.overview && p.overview.length > 0 && (
        <Panel className="mb-6">
          <h2 className="mb-3 font-medium">Tình hình học tập</h2>
          <ClassOverview rows={p.overview} />
        </Panel>
      )}
      <h2 className="mb-2 font-medium">Học sinh</h2>
      <MemberManager classId={id} />
    </>
  );
}
