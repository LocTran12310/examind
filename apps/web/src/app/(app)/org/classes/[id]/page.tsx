"use client";

import Link from "next/link";
import { use, useState } from "react";
import { ClassAdaptiveDialog } from "@/components/adaptive/ClassAdaptiveDialog";
import { ClassOverview } from "@/components/adaptive/ClassOverview";
import { MemberManager } from "@/components/org/MemberManager";
import { FormAlert } from "@/components/app/FormAlert";
import { Button } from "@/components/ui/button";
import { Panel } from "@/components/app/Panel";
import { FormDialog } from "@/components/app/FormDialog";
import { PageHeader } from "@/components/app/PageHeader";
import { useApi } from "@/lib/hooks";
import type { ClassDetail, ClassOverviewRow } from "@/lib/types";

export default function ClassPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { data, reload, error } = useApi<ClassDetail>(`/classes/${id}`);
  const { data: overview, reload: reloadOverview } = useApi<ClassOverviewRow[]>(`/classes/${id}/overview`);
  const [adaptive, setAdaptive] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  if (error) return <p className="text-sm text-destructive">{error}</p>;
  if (!data) return null;
  return (
    <>
      <Link href="/org/classes" className="text-sm text-muted-foreground hover:underline">
        ← Lớp học
      </Link>
      <PageHeader
        title={`Lớp ${data.name}`}
        description={`${data.school_year} · ${data.member_count} học sinh`}
        actions={<Button variant="outline" onClick={() => setAdaptive(true)}>Giao đề ôn cá nhân</Button>}
      />
      {notice && <div className="mb-4"><FormAlert kind="success">{notice}</FormAlert></div>}
      <FormDialog open={adaptive} title="Giao đề ôn cá nhân cho cả lớp" onOpenChange={(o) => !o && setAdaptive(false)}>
        <ClassAdaptiveDialog
          classId={id}
          onDone={(n) => {
            setAdaptive(false);
            setNotice(`Đã tạo ${n} đề ôn riêng cho học sinh.`);
            void reloadOverview();
          }}
        />
      </FormDialog>
      {overview && overview.length > 0 && (
        <Panel className="mb-6">
          <h2 className="mb-3 font-medium">Tình hình học tập</h2>
          <ClassOverview rows={overview} />
        </Panel>
      )}
      <h2 className="mb-2 font-medium">Học sinh</h2>
      <MemberManager classId={id} onChange={reload} />
    </>
  );
}
