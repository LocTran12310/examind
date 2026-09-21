"use client";

import { use } from "react";
import { AssignmentReport } from "@/components/reports/AssignmentReport";
import { PageHeader } from "@/components/ui";
import { useApi } from "@/lib/hooks";
import type { AssignmentReport as Report } from "@/lib/types";

export default function AssignmentReportPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { data } = useApi<Report>(`/assignments/${id}/report`);
  if (!data) return null;
  return (
    <>
      <PageHeader title={data.title} subtitle="Báo cáo bài giao" />
      <AssignmentReport report={data} />
    </>
  );
}
