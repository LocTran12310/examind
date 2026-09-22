"use client";

import { PageHeader } from "@/components/app/PageHeader";
import { useAssignmentReportPage } from "@/hooks/page-hooks/assignment-report/use-assignment-report-page";
import { ReportView } from "./ReportView/ReportView";

export function AssignmentReportPage({ id }: { id: string }) {
  const { report } = useAssignmentReportPage(id);
  if (!report) return null;
  return (
    <>
      <PageHeader title={report.title} description="Báo cáo bài giao" />
      <ReportView report={report} />
    </>
  );
}
