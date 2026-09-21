"use client";

import Link from "next/link";
import { use, useState } from "react";
import { ClassAdaptiveDialog } from "@/components/adaptive/ClassAdaptiveDialog";
import { ClassOverview } from "@/components/adaptive/ClassOverview";
import { MemberManager } from "@/components/org/MemberManager";
import { Alert, Button, Card, Modal, PageHeader } from "@/components/ui";
import { useApi } from "@/lib/hooks";
import type { ClassDetail, ClassOverviewRow } from "@/lib/types";

export default function ClassPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { data, reload, error } = useApi<ClassDetail>(`/classes/${id}`);
  const { data: overview, reload: reloadOverview } = useApi<ClassOverviewRow[]>(`/classes/${id}/overview`);
  const [adaptive, setAdaptive] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  if (error) return <p className="text-sm text-red-700">{error}</p>;
  if (!data) return null;
  return (
    <>
      <Link href="/org/classes" className="text-sm text-gray-500 hover:underline">
        ← Lớp học
      </Link>
      <PageHeader
        title={`Lớp ${data.name}`}
        subtitle={`${data.school_year} · ${data.member_count} học sinh`}
        actions={<Button onClick={() => setAdaptive(true)}>Giao đề ôn cá nhân</Button>}
      />
      {notice && <div className="mb-4"><Alert tone="green">{notice}</Alert></div>}
      <Modal open={adaptive} title="Giao đề ôn cá nhân cho cả lớp" onClose={() => setAdaptive(false)}>
        <ClassAdaptiveDialog
          classId={id}
          onDone={(n) => {
            setAdaptive(false);
            setNotice(`Đã tạo ${n} đề ôn riêng cho học sinh.`);
            void reloadOverview();
          }}
        />
      </Modal>
      {overview && overview.length > 0 && (
        <Card className="mb-6">
          <h2 className="mb-3 font-medium">Tình hình học tập</h2>
          <ClassOverview rows={overview} />
        </Card>
      )}
      <MemberManager detail={data} onChange={reload} />
    </>
  );
}
