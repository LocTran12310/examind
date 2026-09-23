"use client";

import { BackLink } from "@/components/common/BackLink/BackLink";
import { PageHeader } from "@/components/common/PageHeader/PageHeader";
import { useAssignmentReportPage } from "@/hooks/page-hooks/assignment-report/use-assignment-report-page";
import { ReportView } from "./ReportView/ReportView";

export function AssignmentReportPage({ id }: { id: string }) {
  const { report } = useAssignmentReportPage(id);
  if (!report) return null;
  return (
    <>
      {/* a bài giao is reached from its đề thi and the report carries no exam id, so the way back is the exam list */}
      <BackLink href="/org/exams">Đề thi</BackLink>
      <PageHeader title={report.title} description="Báo cáo bài giao" />
      <ReportView report={report} />
    </>
  );
}
